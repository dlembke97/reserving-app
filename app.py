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
    triangles = utils.extract_triangles()

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
            dev_vol = utils.fit_development_model(tri)
            value_tab, ata_tab, exhibit_tab = st.tabs(
                ["Values", "ATA", "Reserve Exhibit"]
            )
            with value_tab:
                st.dataframe(tri.to_frame())
            with ata_tab:
                st.dataframe(tri.link_ratio.to_frame())
                dev_simp = utils.fit_development_model(tri, average="simple")
                ldf_vol = dev_vol.ldf_.to_frame()
                ldf_vol.index = ["Volume Weighted"]
                ldf_simp = dev_simp.ldf_.to_frame()
                ldf_simp.index = ["Simple Average"]
                ldf_table = pd.concat([ldf_vol, ldf_simp])
                st.markdown("**LDFs**")
                st.dataframe(ldf_table)
                cdf_vol = dev_vol.cdf_.to_frame()
                cdf_vol.index = ["Volume Weighted"]
                cdf_simp = dev_simp.cdf_.to_frame()
                cdf_simp.index = ["Simple Average"]
                cdf_table = pd.concat([cdf_vol, cdf_simp])
                st.markdown("**CDFs**")
                st.dataframe(cdf_table)
            with exhibit_tab:
                ultimate_df = dev_vol.ultimate_[val_col].to_frame()
                ultimate_df.columns = ["Ultimate"]
                ultimate_df.index = ultimate_df.index.year
                st.dataframe(ultimate_df)
        st.write("---")


if __name__ == "__main__":
    main()
