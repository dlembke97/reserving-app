import chainladder as cl
import pandas as pd
from typing import Dict, List, Optional, Tuple


class ActuarialUtils:
    """Utility helpers for actuarial reserving tasks."""

    def __init__(self) -> None:
        self.triangle: Optional[cl.Triangle] = None

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

    def fit_development_model(
        self,
        triangle: cl.Triangle,
        **kwargs,
    ) -> cl.Development:
        """Fit a development model to ``triangle``.

        Parameters
        ----------
        triangle:
            The :class:`chainladder.Triangle` to model.
        development_method:
            The development technique to apply. Currently only ``"chainladder"``
            is supported.
        **kwargs:
            Additional keyword arguments forwarded to the underlying
            ``chainladder`` development model.

        Returns
        -------
        chainladder.Development
            The fitted development model instance.
        """

        return cl.Development(**kwargs).fit(triangle)
