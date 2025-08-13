import chainladder as cl
import pandas as pd
from functools import reduce
from typing import Dict, List, Optional, Tuple
import streamlit as st
from pandas.api.types import (
    is_period_dtype,
    is_datetime64_any_dtype,
    is_integer_dtype,
    is_string_dtype,
)
try:  # st_aggrid is optional
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
except Exception:  # pragma: no cover
    AgGrid = GridOptionsBuilder = JsCode = None


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


def custom_aggrid(df: pd.DataFrame) -> dict:
    """Display ``df`` using AG Grid with numeric formatting.

    If ``st_aggrid`` is unavailable the data is rendered using
    :func:`custom_st_dataframe` to avoid runtime errors.
    """

    if GridOptionsBuilder is None:
        custom_st_dataframe(df)
        return {}

    index_levels = df.index.nlevels
    df.columns = df.columns.map(str)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(resizable=True, wrapText=True, autoHeight=True)
    gb.configure_grid_options(domLayout="autoHeight", suppressHorizontalScroll=True)

    numeric_cols = df.select_dtypes(include="number").columns
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
    grid_options["onFirstDataRendered"] = JsCode(
        """
        function(params) {
          let allColumnIds = [];
          params.columnApi.getAllColumns().forEach(c => allColumnIds.push(c.getId()));
          params.columnApi.autoSizeColumns(allColumnIds, false);
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
    return AgGrid(df, gridOptions=grid_options, allow_unsafe_jscode=True)


def custom_st_dataframe(df: pd.DataFrame) -> None:
    """Display ``df`` with numeric formatting via ``st.dataframe``.

    Numeric columns are formatted based on their absolute maximum values. When
    the maximum exceeds ``999`` they are rendered with a thousands separator and
    no decimals; otherwise two decimal places are shown.  Sorting remains
    numeric because the underlying column dtypes are preserved and formatting is
    handled through ``column_config``.
    """

    index_levels = df.index.nlevels
    df = df.copy()
    df.columns = df.columns.map(str)

    numeric_cols = df.select_dtypes(include="number").columns
    index_cols = df.columns[:index_levels]
    numeric_cols = [c for c in numeric_cols if c not in index_cols]

    # Ensure numeric columns are float so missing values (None/pd.NA) don't
    # trigger formatting errors when passed through ``st.column_config``.
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    column_config: dict[str, st.column_config.NumberColumn] = {}
    for col in numeric_cols:
        max_val = df[col].abs().max()
        fmt = "%,.0f" if max_val > 999 else "%,.2f"
        column_config[col] = st.column_config.NumberColumn(format=fmt)

    st.dataframe(df, hide_index=True, column_config=column_config)


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

        # Split into DataFrame representations for each subgroup
        self.triangle_dfs = self.extract_triangle_dfs()
        self.triangle_ata_dfs: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}

        # Compute development factor exhibits for each subgroup
        self.get_dev_factor_exhibit(methods=["volume", "simple"])

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

    def convert_triangle_to_df(
        self, triangle: cl.Triangle, index_name: str = "Year"
    ) -> pd.DataFrame:
        """Convert a ``chainladder.Triangle`` to a DataFrame with a named index column.

        Parameters
        ----------
        triangle:
            Single column ``chainladder.Triangle`` to convert.
        index_name:
            Name to assign to the first column after the index is reset. If
            ``index_name`` is ``"Year"`` (case insensitive) the column is
            coerced to an annual ``PeriodIndex``.

        Returns
        -------
        pd.DataFrame
            ``triangle`` converted to a DataFrame with the index reset and
            renamed column.
        """

        df = triangle.to_frame().reset_index()
        df.rename(columns={df.columns[0]: index_name}, inplace=True)
        if index_name.lower() == "year":
            df[index_name] = pd.PeriodIndex(df[index_name], freq="Y")
        return df

    def convert_and_label_triangle(
        self,
        triangle: cl.Triangle,
        value_name: str,
        index_name: str = "Year",
    ) -> pd.DataFrame:
        """Convert ``triangle`` to a two-column DataFrame with a named value.

        Parameters
        ----------
        triangle:
            Single column ``chainladder.Triangle`` to convert.
        value_name:
            Name to assign to the value column.
        index_name:
            Name to assign to the first column after the index is reset.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the index column and the renamed value column.
        """

        df = self.convert_triangle_to_df(triangle=triangle, index_name=index_name)
        if df.shape[1] >= 2:
            df = df.iloc[:, :2]
            df.rename(columns={df.columns[1]: value_name}, inplace=True)
        return df

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
                    triangles[(group_title, val_col)] = self.convert_triangle_to_df(
                        sub_tri[val_col], index_name="Year"
                    )
        else:
            for val_col in value_cols:
                triangles[(None, val_col)] = self.convert_triangle_to_df(
                    self.triangle[val_col], index_name="Year"
                )

        return triangles

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

    def get_dev_factor_exhibit(self, methods: Optional[List[str]] = None) -> None:
        """Generate LDF and CDF exhibits for each subgroup.

        This method fits development models using the averaging methods
        provided in ``methods`` to every triangle produced by
        :meth:`extract_triangles`. The resulting LDF and CDF tables are stored
        on ``ldf_exhibit`` and ``cdf_exhibit`` dictionaries keyed by
        ``(group_title, value_col)``. The underlying ``chainladder.Triangle``
        objects are also stored on the ``triangles`` attribute for easy access
        when rendering link ratios.

        Parameters
        ----------
        methods:
            List of development averaging methods to apply. Defaults to
            ``["volume", "simple"]``.
        """

        if self.triangle is None:
            raise ValueError("No triangle available. Call create_triangle first.")

        methods = methods or ["volume", "simple"]

        self.triangles = self.extract_triangles()
        self.triangle_ata_dfs: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}
        self.ldf_exhibit: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}
        self.cdf_exhibit: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}

        labels = {"volume": "Volume Weighted", "simple": "Simple Average"}

        for key, tri in self.triangles.items():
            self.triangle_ata_dfs[key] = self.convert_triangle_to_df(
                tri.age_to_age, index_name="Year"
            )
            ldf_dfs: List[pd.DataFrame] = []
            cdf_dfs: List[pd.DataFrame] = []
            for method in methods:
                dev = (
                    cl.Development().fit(tri)
                    if method == "volume"
                    else cl.Development(average=method).fit(tri)
                )
                label = labels.get(method, method.title())
                for attr, dfs in [("ldf_", ldf_dfs), ("cdf_", cdf_dfs)]:
                    df = self.convert_triangle_to_df(
                        getattr(dev, attr), index_name="Avg Method"
                    )
                    df["Avg Method"] = label
                    dfs.append(df)
            self.ldf_exhibit[key] = pd.concat(ldf_dfs)
            self.cdf_exhibit[key] = pd.concat(cdf_dfs)

    def fit_development_model(
        self, development_method: str = "chainladder"
    ) -> Dict[Tuple[Optional[str], str], cl.Pipeline]:
        """Fit a development model to each triangle and return the results.

        Parameters
        ----------
        development_method:
            Reserving technique to apply.  Only ``"chainladder"`` is supported
            at present.

        Returns
        -------
        Dict[Tuple[str | None, str], ``cl.Pipeline``]
            Mapping of ``(group_title, value_col)`` to the fitted model
            pipelines.
        """

        if not hasattr(self, "triangles"):
            self.triangles = self.extract_triangles()

        self.fitted_models: Dict[Tuple[Optional[str], str], cl.Pipeline] = {}

        for key, tri in self.triangles.items():
            if development_method.lower() == "chainladder":
                pipe = cl.Pipeline([("chainladder", cl.Chainladder())]).fit(tri)
                self.fitted_models[key] = pipe
            else:
                raise ValueError(
                    f"Unsupported development method: {development_method}"
                )

        return self.fitted_models

    def get_reserve_exhibit(
        self, prem_col: Optional[str] = None
    ) -> Dict[Tuple[Optional[str], str], pd.DataFrame]:
        """Return reserve exhibits using previously fitted development models.

        Parameters
        ----------
        prem_col:
            Optional premium column included in ``value_cols``.  When provided,
            the premium's latest diagonal is added as the first column of the
            reserve exhibit and separate exhibits for the premium column are
            omitted.
        """

        if not hasattr(self, "fitted_models"):
            raise ValueError(
                "No fitted models available. Call fit_development_model first."
            )

        premium_dfs: Dict[Optional[str], pd.DataFrame] = {}
        if prem_col:
            for (group_title, val_col), tri in self.triangles.items():
                if val_col == prem_col:
                    premium_dfs[group_title] = self.convert_and_label_triangle(
                        triangle=tri.latest_diagonal,
                        value_name=prem_col,
                        index_name="Year",
                    )

        self.reserve_exhibit: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}

        for key, model in self.fitted_models.items():
            group_title, val_col = key
            if val_col == prem_col:
                continue

            tri = self.triangles[key]

            ultimate_df = self.convert_and_label_triangle(
                triangle=model["chainladder"].ultimate_,
                value_name="Chainladder Ultimate",
                index_name="Year",
            )

            latest_df = self.convert_and_label_triangle(
                triangle=tri.latest_diagonal,
                value_name=val_col,
                index_name="Year",
            )

            premium_df = premium_dfs.get(group_title)

            frames = [f for f in [premium_df, latest_df, ultimate_df] if f is not None]
            self.reserve_exhibit[key] = reduce(
                lambda left, right: pd.merge(left, right, on="Year", how="outer"),
                frames,
            )

        return self.reserve_exhibit
