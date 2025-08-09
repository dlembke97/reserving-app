import chainladder as cl
import pandas as pd
from typing import Dict, List, Optional, Tuple


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
        self.triangle_dfs = self.extract_triangle_dfs()

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
                    triangles[(group_title, val_col)] = sub_tri[val_col].to_frame()
        else:
            for val_col in value_cols:
                triangles[(None, val_col)] = self.triangle[val_col].to_frame()
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
            ldf_vol.index = ["Volume Weighted"]
            ldf_simp = dev_simp.ldf_.to_frame()
            ldf_simp.index = ["Simple Average"]
            self.ldf_exhibit[key] = pd.concat([ldf_vol, ldf_simp])

            cdf_vol = dev_vol.cdf_.to_frame()
            cdf_vol.index = ["Volume Weighted"]
            cdf_simp = dev_simp.cdf_.to_frame()
            cdf_simp.index = ["Simple Average"]
            self.cdf_exhibit[key] = pd.concat([cdf_vol, cdf_simp])
