import streamlit as st
import chainladder as cl
import pandas as pd


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

    # Determine numeric value columns
    value_cols = [col for col in df.columns if col not in ["origin", "development"] + cat_cols]

    # Sidebar allowing user to select grouping columns
    group_cols = st.sidebar.multiselect("Group triangles by", cat_cols)

    # Display triangles for each unique combination of selected categories
    if group_cols:
        for key, group in df.groupby(group_cols):
            key_vals = key if isinstance(key, tuple) else (key,)
            title = ", ".join(f"{col}={val}" for col, val in zip(group_cols, key_vals))
            st.subheader(title)
            sub_triangle = cl.Triangle(
                data=group,
                origin="origin",
                development="development",
                columns=value_cols,
                index=group_cols,
                cumulative=True,
            )
            st.dataframe(sub_triangle.to_frame())
    else:
        st.dataframe(df)


if __name__ == "__main__":
    main()
