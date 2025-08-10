import chainladder as cl
import pandas as pd
import streamlit as st

from helper_functions import *


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

    utils = ReservingAppTriangle(
        df,
        origin="origin",
        development="development",
        value_cols=selected_values,
        group_cols=group_cols,
        cumulative=True,
    )
    utils.fit_development_model()
    triangles = utils.triangles

    # Restructure triangles so that each grouping combination renders its
    # associated value column triangles together rather than as individual
    # entries.  ``triangles`` is keyed by ``(group_title, value_col)``; group
    # them by ``group_title`` first, then iterate the value columns within
    # each group.
    grouped: dict[str | None, dict[str, cl.Triangle]] = {}
    for (group_title, val_col), tri in triangles.items():
        grouped.setdefault(group_title, {})[val_col] = tri

    for group_title, val_map in grouped.items():
        if group_title is not None:
            st.subheader(group_title)
        for val_col, tri in val_map.items():
            # When no grouping columns are supplied, the value column itself
            # should serve as the subheader.  Otherwise, display the value
            # column as a caption within the group section.
            if group_title is None:
                st.subheader(val_col)
            else:
                st.markdown(f"**{val_col}**")
            value_tab, ata_tab, reserve_tab = st.tabs(["Values", "ATA", "Reserve Exhibit"])
            with value_tab:
                custom_aggrid(tri.to_frame(), index_label="Year")
            with ata_tab:
                custom_aggrid(tri.link_ratio.to_frame(), index_label="Year")
                st.markdown("**LDFs**")
                custom_aggrid(utils.ldf_exhibit[(group_title, val_col)], index_label="Year")
                st.markdown("**CDFs**")
                custom_aggrid(utils.cdf_exhibit[(group_title, val_col)], index_label="Year")
            with reserve_tab:
                custom_aggrid(utils.reserve_exhibit[(group_title, val_col)], index_label="Year")
        st.write("---")


if __name__ == "__main__":
    main()
