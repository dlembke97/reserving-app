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

        df = self.triangle.to_frame().reset_index()
        origin = self.triangle.origin
        development = self.triangle.development
        group_cols = [name for name in self.triangle.index.names if name is not None]
        value_cols = list(self.triangle.columns)

        triangles: Dict[Tuple[Optional[str], str], pd.DataFrame] = {}
        if group_cols:
            for key, grp in df.groupby(group_cols):
                key_vals = key if isinstance(key, tuple) else (key,)
                group_title = ", ".join(
                    f"{col}={val}" for col, val in zip(group_cols, key_vals)
                )
                for val_col in value_cols:
                    pivot = grp.pivot(
                        index=origin, columns=development, values=val_col
                    )
                    triangles[(group_title, val_col)] = pivot
        else:
            for val_col in value_cols:
                pivot = df.pivot(index=origin, columns=development, values=val_col)
                triangles[(None, val_col)] = pivot
        return triangles
