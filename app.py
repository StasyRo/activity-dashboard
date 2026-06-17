import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Activity Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Activity Dashboard - Test mode")

DATA_FILE = Path("Data.xlsx")

st.write("Checking Excel file...")

if not DATA_FILE.exists():
    st.error("File latest_activities.xlsx was not found.")
    st.stop()

st.success("Excel file was found.")

try:
    df = pd.read_excel(DATA_FILE, engine="openpyxl")
    df.columns = df.columns.str.strip()

    st.success("Excel file was opened successfully.")

    st.subheader("Columns found in your Excel file:")
    st.write(list(df.columns))

    st.subheader("Number of rows:")
    st.write(len(df))

    st.subheader("First 5 rows:")
    st.dataframe(df.head(5), use_container_width=True)

except Exception as e:
    st.error("Excel file could not be opened.")
    st.write("Error type:")
    st.code(type(e).__name__)
    st.write("Error message:")
    st.code(str(e))
