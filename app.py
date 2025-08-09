import streamlit as st
import chainladder as cl


def main():
    st.title("Claims Triangle")

    # Load sample data as a Triangle and retrieve the underlying tabular data
    triangle = cl.load_sample("RAA")
    df = triangle.to_frame(keepdims=True)

    # Identify categorical columns that can be used for grouping
    cat_cols = [
        col
        for col, dtype in df.dtypes.items()
        if dtype == "object" and col not in ["origin", "development", "values"]
    ]

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
                columns=["values"],
                index=group_cols,
            )
            st.dataframe(sub_triangle.to_frame())
    else:
        st.dataframe(triangle.to_frame())


if __name__ == "__main__":
    main()
