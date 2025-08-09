import chainladder as cl
import pandas as pd
import streamlit as st

from helper_functions import ActuarialUtils


def process_data() -> tuple[pd.DataFrame, list[str]]:
    """Load sample data and derive categorical columns for grouping.

    Returns a tuple of the processed DataFrame and a list of categorical
    column names that can be used for grouping in the sidebar.
    """

    triangle = cl.load_sample("clrd")
    df = triangle.to_frame().reset_index()
    df["development"] = df.apply(
        lambda row: row["origin"] + pd.DateOffset(months=int(row["development"]) - 12),
        axis=1,
    )
    cat_cols = [
        col
        for col, dtype in df.dtypes.items()
        if dtype == "object" and col not in ["origin", "development"]
    ]
    return df, cat_cols


def render_sidebar(cat_cols: list[str]) -> tuple[list[str], list[str]]:
    """Render sidebar controls and return user selections."""

    value_options = ["IncurLoss", "CumPaidLoss"]
    selected_values = st.sidebar.multiselect(
        "Value columns", value_options, default=value_options
    )
    group_cols = st.sidebar.multiselect("Group triangles by", cat_cols)
    return selected_values, group_cols


def main() -> None:
    """Streamlit application entry point."""

    st.title("Claims Triangle")
    df, cat_cols = process_data()
    selected_values, group_cols = render_sidebar(cat_cols)

    utils = ActuarialUtils()
    utils.create_triangle(
        df,
        origin="origin",
        development="development",
        value_cols=selected_values,
        group_cols=group_cols,
        cumulative=True,
    )
    triangles = utils.extract_triangle_dfs()

    # Restructure triangles so that each grouping combination renders its
    # associated value column triangles together rather than as individual
    # entries.  ``triangles`` is keyed by ``(group_title, value_col)``; group
    # them by ``group_title`` first, then iterate the value columns within
    # each group.
    grouped: dict[str | None, dict[str, pd.DataFrame]] = {}
    for (group_title, val_col), tri_df in triangles.items():
        grouped.setdefault(group_title, {})[val_col] = tri_df

    for group_title, val_map in grouped.items():
        if group_title is not None:
            st.subheader(group_title)
        for val_col, tri_df in val_map.items():
            # When no grouping columns are supplied, the value column itself
            # should serve as the subheader.  Otherwise, display the value
            # column as a caption within the group section.
            if group_title is None:
                st.subheader(val_col)
            else:
                st.markdown(f"**{val_col}**")
            st.dataframe(tri_df)


if __name__ == "__main__":
    main()
