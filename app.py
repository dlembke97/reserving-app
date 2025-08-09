import pandas as pd
import streamlit as st
import chainladder as cl

st.set_page_config(page_title="Reserving App", page_icon="📊")


def load_uploaded_triangle(file):
    df = pd.read_csv(file, index_col=0)
    return cl.Triangle(df), df


def load_sample_triangle():
    clrd = cl.load_sample("clrd")
    index = clrd.index
    group_by = st.selectbox("Group by", ["Company", "Line of Business"])
    measure = st.selectbox("Value", clrd.columns.tolist(), index=1)
    if group_by == "Company":
        companies = sorted(index["GRNAME"].unique())
        company = st.selectbox("Company", companies)
        lob_options = sorted(index.loc[index["GRNAME"] == company, "LOB"].unique())
        lob = st.selectbox("Line of Business", lob_options)
        triangle = clrd.loc[(company, lob), measure]
        title = f"{measure} - {company} - {lob}"
    else:
        lobs = sorted(index["LOB"].unique())
        lob = st.selectbox("Line of Business", lobs)
        triangle = clrd.groupby("LOB").sum().loc[lob, measure]
        title = f"{measure} - {lob}"
    st.subheader(title)
    st.dataframe(triangle.to_frame())
    return triangle


def triangle_tab():
    st.header("Triangle Builder")
    uploaded = st.file_uploader("Triangle CSV", type="csv")
    if uploaded:
        triangle, df = load_uploaded_triangle(uploaded)
        st.subheader("Input Triangle")
        st.dataframe(df)
    else:
        st.info("Using sample CLRD dataset")
        triangle = load_sample_triangle()
    return triangle


def ldf_cdf_tab(triangle):
    st.header("LDF/CDF Analysis")
    if triangle is None:
        st.warning("Please build a triangle in the previous tab.")
        return
    model = cl.Chainladder().fit(triangle)
    display = st.multiselect("Display", ["LDF", "CDF"], default=["LDF", "CDF"])
    if "LDF" in display:
        ldf_values = model.ldf_.values[0, 0, 0][:-1]
        ldfs = pd.Series(ldf_values, index=triangle.development, name="LDF")
        st.subheader("Loss Development Factors")
        st.dataframe(ldfs)
    if "CDF" in display:
        cdf_values = model.cdf_.values[0, 0, 0][:-1]
        cdfs = pd.Series(cdf_values, index=triangle.development, name="CDF")
        st.subheader("Cumulative Development Factors")
        st.dataframe(cdfs)
    st.subheader("Ultimate Claims")
    ultimate = model.ultimate_.to_frame()
    ultimate.columns = ["ultimate"]
    st.dataframe(ultimate)
    st.subheader("IBNR by Origin Period")
    ibnr = model.ibnr_.to_frame()
    ibnr.columns = ["ibnr"]
    st.dataframe(ibnr)
    st.metric("Total IBNR", f"{ibnr['ibnr'].sum():,.0f}")


def main():
    st.title("Chain Ladder Reserving App")
    tabs = st.tabs(["Triangle", "LDF/CDF"])
    with tabs[0]:
        triangle = triangle_tab()
    with tabs[1]:
        ldf_cdf_tab(triangle)


if __name__ == "__main__":
    main()
