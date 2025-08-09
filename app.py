import streamlit as st
import chainladder as cl
import pandas as pd

from helper_functions import ActuarialUtils


def main():
    st.title("Claims Triangle")

    # Load sample data with multiple value columns and index categories
    triangle = cl.load_sample("clrd")
    df = triangle.to_frame().reset_index()

    # Convert numeric development lags to actual evaluation dates
    df["development"] = df.apply(
        lambda row: row["origin"] + pd.DateOffset(months=int(row["development"])),
        axis=1,
    )

    # Identify categorical columns that can be used for grouping
    cat_cols = [
        col
        for col, dtype in df.dtypes.items()
        if dtype == "object" and col not in ["origin", "development"]
    ]

    # Sidebar allowing user to select value and grouping columns
    value_options = ["IncurLoss", "CumPaidLoss"]
    selected_values = st.sidebar.multiselect(
        "Value columns", value_options, default=value_options
    )
    group_cols = st.sidebar.multiselect("Group triangles by", cat_cols)

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
