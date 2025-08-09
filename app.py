import streamlit as st
import chainladder as cl


def main():
    st.title("Claims Triangle")
    triangle = cl.load_sample("RAA")
    st.dataframe(triangle.to_frame())


if __name__ == "__main__":
    main()
