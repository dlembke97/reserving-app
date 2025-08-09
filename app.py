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
        lambda row: row["origin"] + pd.DateOffset(months=int(row["development"])),
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

    for (group_title, val_col), tri_df in triangles.items():
        title_parts = [val_col]
        if group_title:
            title_parts.insert(0, group_title)
        st.subheader(" - ".join(title_parts))
        st.dataframe(tri_df)


if __name__ == "__main__":
    main()
