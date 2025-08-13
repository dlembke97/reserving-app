import chainladder as cl
import pandas as pd
from typing import Dict, List, Optional, Tuple
import streamlit as st
from pandas.api.types import (
    is_period_dtype,
    is_datetime64_any_dtype,
    is_integer_dtype,
    is_string_dtype,
)
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


def _coerce_year_column(df: pd.DataFrame, colname: str = "Year") -> pd.DataFrame:
    df = df.copy()

    # ensure "Year" exists (might be in the index)
    if colname not in df.columns:
        df = df.reset_index().rename(columns={"index": colname})

    col = df[colname]

    if is_period_dtype(col):
        # Period -> timestamp -> year
        y = col.dt.to_timestamp().dt.year
    elif is_datetime64_any_dtype(col):
        # datetime64[ns] (or tz-aware)
        y = (
            col.dt.tz_localize(None) if getattr(col.dt, "tz", None) is not None else col
        ).dt.year
    else:
        # try to parse strings/numbers into datetimes; if that fails, fall back to numeric year
        parsed = pd.to_datetime(col, errors="coerce")
        if parsed.notna().any():
            y = parsed.dt.year
        else:
            y = pd.to_numeric(col, errors="coerce")

    # keep nullable ints so missing years don’t crash
    df[colname] = y.astype("Int64")
    return df


def _json_safe(df: pd.DataFrame) -> pd.DataFrame:
    """
    AgGrid sends data as JSON; JSON can't contain NaN/Infinity/<NA>.
    Convert all missing to None and avoid NumPy scalars that serialize to NaN.
    """
    df = df.copy()
    # Convert pandas NA/NaN to None
    df = df.where(df.notna(), None)
    # Make sure nullable integers don’t re-emit NaN; cast each column to Python objects
    for c in df.columns:
        if pd.api.types.is_integer_dtype(df[c]) and str(df[c].dtype).startswith("Int"):
            df[c] = df[c].astype(object)  # keeps None for missing
    return df


def convert_triangle_to_df(triangle: cl.Triangle) -> pd.DataFrame:
    """Convert a ``chainladder.Triangle`` to a DataFrame with a ``Year`` column.

    Parameters
    ----------
    triangle:
        Single column ``chainladder.Triangle`` to convert.

    Returns
    -------
    pd.DataFrame
        ``triangle`` converted to a DataFrame with the index reset, the first
        column renamed to ``Year`` and coerced to an annual ``PeriodIndex``.
    """

    df = triangle.to_frame().reset_index()
    df.rename(columns={df.columns[0]: "Year"}, inplace=True)
    df["Year"] = pd.PeriodIndex(df["Year"], freq="Y")
    return df


def custom_aggrid(df: pd.DataFrame, index_label: Optional[str] = None) -> dict:
    """Display ``df`` using AG Grid with numeric formatting.

    The index is rendered as standard columns so that it appears in the grid
    output.  All column labels are coerced to strings to avoid JavaScript
    errors when numeric column names are encountered.

    Numeric columns are formatted depending on whether their absolute maximum
    value exceeds 999. Values greater than this threshold are shown with a
    thousands separator and no decimals. Otherwise values are displayed with
    two decimal places. Sorting remains based on the underlying numeric value
    via ``valueFormatter`` JavaScript functions.

    Parameters
    ----------
    df:
        DataFrame to render.
    index_label:
        Optional name to use for the index column once rendered.  When
        provided, this replaces the existing index name after reset.

    Returns
    -------
    dict
        Response returned by :func:`st_aggrid.AgGrid`.
    """

    # Display the index as regular columns and ensure all column labels are
    # strings so that AG Grid's internal string operations do not fail on
    # numeric names.
    index_levels = df.index.nlevels
    df.columns = df.columns.map(str)

    df = _json_safe(df)
    gb = GridOptionsBuilder.from_dataframe(df)

    # Make columns resizable & allow wrapping if needed
    gb.configure_default_column(resizable=True, wrapText=True, autoHeight=True)

    # Let the grid grow to content height and avoid horizontal scroll
    gb.configure_grid_options(domLayout="autoHeight", suppressHorizontalScroll=True)

    numeric_cols = df.select_dtypes(include="number").columns
    # Exclude index columns from numeric formatting to preserve values like
    # "1990" without thousands separators.
    index_cols = df.columns[:index_levels]
    numeric_cols = [col for col in numeric_cols if col not in index_cols]
    for col in numeric_cols:
        max_val = df[col].abs().max()
        if max_val > 999:
            formatter = JsCode(
                "function(params) {return Number(params.value).toLocaleString('en-US', "
                "{minimumFractionDigits:0, maximumFractionDigits:0});}"
            )
        else:
            formatter = JsCode(
                "function(params) {return Number(params.value).toLocaleString('en-US', "
                "{minimumFractionDigits:2, maximumFractionDigits:2});}"
            )
        gb.configure_column(col, type=["numericColumn"], valueFormatter=formatter)

    grid_options = gb.build()
    # Autosize to content, then fit to container, and keep responsive
    grid_options["onFirstDataRendered"] = JsCode(
        """
        function(params) {
          let allColumnIds = [];
          params.columnApi.getAllColumns().forEach(c => allColumnIds.push(c.getId()));
          // 1) Measure real content widths
          params.columnApi.autoSizeColumns(allColumnIds, false);
          // 2) Then fill the remaining viewport neatly
          params.api.sizeColumnsToFit();
        }
    """
    )
    grid_options["onGridSizeChanged"] = JsCode(
        """
        function(params) {
          params.api.sizeColumnsToFit();
        }
    """
    )
    st.dataframe(df, hide_index=True)
    # return AgGrid(df, gridOptions=grid_options, allow_unsafe_jscode=True)


class ReservingAppTriangle:
    """Utility helpers for actuarial reserving tasks.

    On instantiation this class immediately builds a ``chainladder`` triangle
    from the provided data, extracts each subgroup as a DataFrame and computes
    development factor exhibits.  The resulting artifacts are exposed via the
    ``triangle`` ``triangle_dfs``, ``triangles``, ``ldf_exhibit`` and
    ``cdf_exhibit`` attributes.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        origin: str = "origin",
        development: str = "development",
        value_cols: Optional[List[str]] = None,
        group_cols: Optional[List[str]] = None,
        cumulative: bool = True,
    ) -> None:
        # Build and store the master triangle
        self.triangle: cl.Triangle = self.create_triangle(
            data,
            origin=origin,
            development=development,
            value_cols=value_cols,
            group_cols=group_cols,
            cumulative=cumulative,
        )

        # Split into DataFrame and Triangle representations for each subgroup
        self.triangle_dfs, self.triangle_ata_dfs = self.extract_triangle_dfs()

        # Compute development factor exhibits for each subgroup
        self.get_dev_factor_exhibit()

    def create_triangle(
        self,
        data: pd.DataFrame,
        origin: str = "origin",
        development: str = "development",
        value_cols: Optional[List[str]] = None,
        group_cols: Optional[List[str]] = None,
        cumulative: bool = True,
    ) -> cl.Triangle:
        """Create and store a ``chainladder.Triangle`` from ``data``."""

        value_cols = value_cols or [
            col
            for col in data.columns
            if col not in [origin, development] + (group_cols or [])
        ]

        self.triangle = cl.Triangle(
            data=data,
            origin=origin,
            development=development,
            columns=value_cols,
            index=group_cols,
            cumulative=cumulative,
        )
        return self.triangle

    def extract_triangle_dfs(
        self,
    ) -> Dict[Tuple[Optional[str], str], pd.DataFrame]:
        """Return DataFrames for each value column and group combination.

        ``create_triangle`` must be called before invoking this method. The
        stored triangle is split into a dictionary keyed by ``(group_key,
        value_col)`` where ``group_key`` is a formatted string of the grouping
        column values or ``None`` when no grouping columns were supplied.
        """

        if self.triangle is None:
            raise ValueError("No triangle available. Call create_triangle first.")

        # ``chainladder.Triangle`` exposes its grouping keys via a DataFrame on the
        # ``index`` attribute rather than a ``MultiIndex``.  Attempting to access
        # ``index.names`` therefore raises ``AttributeError``.  Instead, rely on the
        # DataFrame column labels and drop the synthetic ``Total`` column that
        # Chainladder adds when no explicit grouping columns are supplied.
        index_df = self.triangle.index
        group_cols = [
            col
            for col in index_df.columns
            if not (col == "Total" and index_df[col].nunique() == 1)
        ]

        value_cols = list(self.triangle.columns)

        triangles: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}
        triangle_atas: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}
        group_title = None
        if group_cols:
            unique_groups = index_df[group_cols].drop_duplicates()
            for row in unique_groups.itertuples(index=False, name=None):
                sub_tri = self.triangle
                for col, val in zip(group_cols, row):
                    sub_tri = sub_tri[sub_tri[col] == val]
                group_title = ", ".join(
                    f"{col}={val}" for col, val in zip(group_cols, row)
                )
                for val_col in value_cols:
                    triangles[(group_title, val_col)] = convert_triangle_to_df(
                        sub_tri[val_col]
                    )
                    triangle_atas[(group_title, val_col)] = convert_triangle_to_df(
                        sub_tri[val_col].link_ratio
                    )
        else:
            for val_col in value_cols:
                triangles[(None, val_col)] = convert_triangle_to_df(
                    self.triangle[val_col]
                )
                triangle_atas[(None, val_col)] = convert_triangle_to_df(
                    sub_tri[val_col].link_ratio
                )

        return triangles, triangle_atas

    def extract_triangles(
        self,
    ) -> Dict[Tuple[Optional[str], str], cl.Triangle]:
        """Return ``chainladder.Triangle`` objects for each subgroup.

        The keys of the returned dictionary match those from
        :meth:`extract_triangle_dfs` but the values are the underlying
        ``chainladder.Triangle`` instances rather than the DataFrame
        representation.  This is helpful for computing age‑to‑age factors
        and development statistics without repeatedly converting between
        object types.
        """

        if self.triangle is None:
            raise ValueError("No triangle available. Call create_triangle first.")

        index_df = self.triangle.index
        group_cols = [
            col
            for col in index_df.columns
            if not (col == "Total" and index_df[col].nunique() == 1)
        ]

        value_cols = list(self.triangle.columns)

        triangles: Dict[Tuple[Optional[str], str], cl.Triangle] = {}
        if group_cols:
            unique_groups = index_df[group_cols].drop_duplicates()
            for row in unique_groups.itertuples(index=False, name=None):
                sub_tri = self.triangle
                for col, val in zip(group_cols, row):
                    sub_tri = sub_tri[sub_tri[col] == val]
                group_title = ", ".join(
                    f"{col}={val}" for col, val in zip(group_cols, row)
                )
                for val_col in value_cols:
                    triangles[(group_title, val_col)] = sub_tri[val_col]
        else:
            for val_col in value_cols:
                triangles[(None, val_col)] = self.triangle[val_col]
        return triangles

    def get_dev_factor_exhibit(self) -> None:
        """Generate LDF and CDF exhibits for each subgroup.

        This method fits both volume weighted and simple average development
        models to every triangle produced by :meth:`extract_triangles`.  The
        resulting LDF and CDF tables are stored on ``ldf_exhibit`` and
        ``cdf_exhibit`` dictionaries keyed by ``(group_title, value_col)``.
        The underlying ``chainladder.Triangle`` objects are also stored on the
        ``triangles`` attribute for easy access when rendering link ratios.
        """

        if self.triangle is None:
            raise ValueError("No triangle available. Call create_triangle first.")

        self.triangles = self.extract_triangles()
        self.ldf_exhibit: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}
        self.cdf_exhibit: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}

        for key, tri in self.triangles.items():
            dev_vol = cl.Development().fit(tri)
            dev_simp = cl.Development(average="simple").fit(tri)

            ldf_vol = dev_vol.ldf_.to_frame()
            ldf_vol["Avg Method"] = ["Volume Weighted"]
            ldf_simp = dev_simp.ldf_.to_frame()
            ldf_simp["Avg Method"] = ["Simple Average"]
            self.ldf_exhibit[key] = pd.concat([ldf_vol, ldf_simp])

            cdf_vol = dev_vol.cdf_.to_frame()
            cdf_vol["Avg Method"] = ["Volume Weighted"]
            cdf_simp = dev_simp.cdf_.to_frame()
            cdf_simp["Avg Method"] = ["Simple Average"]
            self.cdf_exhibit[key] = pd.concat([cdf_vol, cdf_simp])

    def fit_development_model(
        self, development_method: str = "chainladder", prem_col: Optional[str] = None
    ) -> None:
        """Fit a development model and store resulting exhibits.

        Currently supports only the deterministic Chainladder method.  For each
        triangle derived from :meth:`extract_triangles`, a ``Pipeline`` is used
        to fit the selected development model and the ultimate losses by origin
        year are captured on the ``reserve_exhibit`` attribute.

        Parameters
        ----------
        development_method:
            Reserving technique to apply.  Only ``"chainladder"`` is supported
            at present.
        prem_col:
            Optional premium column included in ``value_cols``.  When provided,
            the premium's latest diagonal is added as the second column of the
            reserve exhibit and separate exhibits for the premium column are
            omitted.
        """

        if not hasattr(self, "triangles"):
            self.triangles = self.extract_triangles()

        self.reserve_exhibit: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}

        for key, tri in self.triangles.items():
            group_title, val_col = key
            if val_col == prem_col:
                continue

            if development_method.lower() == "chainladder":
                pipe = cl.Pipeline([("chainladder", cl.Chainladder())]).fit(tri)
                ultimate_df = pipe["chainladder"].ultimate_.to_frame()
                if len(ultimate_df.columns) == 1:
                    ultimate_df.columns = ["Ultimate"]

                premium_df = None
                if prem_col and (group_title, prem_col) in self.triangles:
                    premium_df = self.triangles[
                        (group_title, prem_col)
                    ].latest_diagonal.to_frame(prem_col)
                latest_df = tri.latest_diagonal.to_frame(val_col)
                frames = [
                    f for f in [premium_df, latest_df, ultimate_df] if f is not None
                ]
                self.reserve_exhibit[key] = pd.concat(frames, axis=1)
            else:
                raise ValueError(
                    f"Unsupported development method: {development_method}"
                )
