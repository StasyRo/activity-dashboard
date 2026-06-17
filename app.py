import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Activity Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Activity Dashboard")
st.caption("Overview of participants by donor, location and activity")

DATA_FILE = Path("Data.xlsx")

if not DATA_FILE.exists():
    st.error("Excel file Data.xlsx was not found.")
    st.stop()

df = pd.read_excel(DATA_FILE, engine="openpyxl")
df.columns = df.columns.str.strip()

required_columns = [
    "Date",
    "Oblast",
    "Rayon",
    "Hromada",
    "Gender",
    "Displacement",
    "Disability",
    "Office",
    "ActDis",
    "Donor number",
    "Activity"
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("Missing required columns:")
    st.write(missing_columns)

    st.subheader("Columns found in your Excel:")
    st.write(list(df.columns))
    st.stop()

# Clean data
for col in required_columns:
    df[col] = df[col].fillna("Not specified").astype(str).str.strip()

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")


def get_options(dataframe, column):
    return sorted(dataframe[column].dropna().astype(str).unique().tolist())


st.sidebar.header("Filters")

donors = get_options(df, "Donor number")
offices = get_options(df, "Office")
oblasts = get_options(df, "Oblast")
activities = get_options(df, "Activity")
gender = get_options(df, "Gender")
disability = get_options(df, "Disability")
displacement = get_options(df, "Displacement")

selected_donors = st.sidebar.multiselect("Donor", donors, default=donors)
selected_offices = st.sidebar.multiselect("Office", offices, default=offices)
selected_oblasts = st.sidebar.multiselect("Oblast", oblasts, default=oblasts)
selected_activities = st.sidebar.multiselect("Activity", activities, default=activities)
selected_gender = st.sidebar.multiselect("Gender", gender, default=gender)
selected_disability = st.sidebar.multiselect("Disability", disability, default=disability)
selected_displacement = st.sidebar.multiselect("Displacement", displacement, default=displacement)

filtered_df = df[
    df["Donor number"].isin(selected_donors) &
    df["Office"].isin(selected_offices) &
    df["Oblast"].isin(selected_oblasts) &
    df["Activity"].isin(selected_activities) &
    df["Gender"].isin(selected_gender) &
    df["Disability"].isin(selected_disability) &
    df["Displacement"].isin(selected_displacement)
]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total participants", len(filtered_df))
col2.metric("Donors", filtered_df["Donor number"].nunique())
col3.metric("Activities", filtered_df["Activity"].nunique())
col4.metric("Hromadas", filtered_df["Hromada"].nunique())

st.divider()

if filtered_df.empty:
    st.warning("No data for selected filters.")
    st.stop()


def make_bar(dataframe, group_column, title):
    summary = (
        dataframe.groupby(group_column, dropna=False)
        .size()
        .reset_index(name="Participants")
        .sort_values("Participants", ascending=False)
    )

    summary[group_column] = summary[group_column].astype(str)

    fig = px.bar(
        summary,
        x=group_column,
        y="Participants",
        text="Participants",
        title=title
    )

    st.plotly_chart(fig, use_container_width=True)


def make_pie(dataframe, group_column, title):
    summary = (
        dataframe.groupby(group_column, dropna=False)
        .size()
        .reset_index(name="Participants")
        .sort_values("Participants", ascending=False)
    )

    summary[group_column] = summary[group_column].astype(str)

    fig = px.pie(
        summary,
        names=group_column,
        values="Participants",
        title=title
    )

    st.plotly_chart(fig, use_container_width=True)


make_bar(filtered_df, "Donor number", "Participants by donor")
make_bar(filtered_df, "Activity", "Participants by activity")
make_bar(filtered_df, "Oblast", "Participants by oblast")
make_bar(filtered_df, "Hromada", "Participants by hromada")

make_pie(filtered_df, "Gender", "Gender breakdown")
make_pie(filtered_df, "Displacement", "Displacement status")
make_pie(filtered_df, "Disability", "Disability status")

st.subheader("Detailed data")
st.dataframe(filtered_df, use_container_width=True)

with st.expander("Technical check"):
    st.write("Total rows in file:", len(df))
    st.write("Columns:", list(df.columns))
