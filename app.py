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
st.caption("Overview of activities by donor, location and participant profile")

DATA_FILE = Path("Data.xlsx")

if not DATA_FILE.exists():
    st.error("Excel file not found. Please upload latest_activities.xlsx to GitHub.")
    st.stop()

df = pd.read_excel(DATA_FILE)
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
    st.error(f"Missing required columns: {', '.join(missing_columns)}")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

st.sidebar.header("Filters")

donors = sorted(df["Donor number"].dropna().unique())
offices = sorted(df["Office"].dropna().unique())
oblasts = sorted(df["Oblast"].dropna().unique())
activities = sorted(df["Activity"].dropna().unique())

selected_donors = st.sidebar.multiselect(
    "Donor",
    donors,
    default=donors
)

selected_offices = st.sidebar.multiselect(
    "Office",
    offices,
    default=offices
)

selected_oblasts = st.sidebar.multiselect(
    "Oblast",
    oblasts,
    default=oblasts
)

selected_activities = st.sidebar.multiselect(
    "Activity",
    activities,
    default=activities
)

filtered_df = df[
    df["Donor number"].isin(selected_donors) &
    df["Office"].isin(selected_offices) &
    df["Oblast"].isin(selected_oblasts) &
    df["Activity"].isin(selected_activities)
]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total records", len(filtered_df))
col2.metric("Donors", filtered_df["Donor number"].nunique())
col3.metric("Activities", filtered_df["Activity"].nunique())
col4.metric("Hromadas", filtered_df["Hromada"].nunique())

st.divider()

if filtered_df.empty:
    st.warning("No data for selected filters.")
    st.stop()

donor_summary = (
    filtered_df.groupby("Donor number", as_index=False)
    .size()
    .rename(columns={"size": "Participants"})
    .sort_values("Participants", ascending=False)
)

fig_donor = px.bar(
    donor_summary,
    x="Donor number",
    y="Participants",
    text="Participants",
    title="Participants by donor"
)

st.plotly_chart(fig_donor, use_container_width=True)

activity_summary = (
    filtered_df.groupby("Activity", as_index=False)
    .size()
    .rename(columns={"size": "Participants"})
    .sort_values("Participants", ascending=False)
)

fig_activity = px.bar(
    activity_summary,
    x="Activity",
    y="Records",
    text="Participants",
    title="Participants by activity"
)

st.plotly_chart(fig_activity, use_container_width=True)

oblast_summary = (
    filtered_df.groupby("Oblast", as_index=False)
    .size()
    .rename(columns={"size": "Participants"})
    .sort_values("Participants", ascending=False)
)

fig_oblast = px.bar(
    oblast_summary,
    x="Oblast",
    y="Participants",
    text="Participants",
    title="Participants by oblast"
)

st.plotly_chart(fig_oblast, use_container_width=True)

gender_summary = (
    filtered_df.groupby("Gender", as_index=False)
    .size()
    .rename(columns={"size": "Participants"})
    .sort_values("Participants", ascending=False)
)

fig_gender = px.pie(
    gender_summary,
    names="Gender",
    values="Participants",
    title="Gender breakdown"
)

st.plotly_chart(fig_gender, use_container_width=True)

displacement_summary = (
    filtered_df.groupby("Displacement", as_index=False)
    .size()
    .rename(columns={"size": "Participants"})
    .sort_values("Participants", ascending=False)
)

fig_displacement = px.pie(
    displacement_summary,
    names="Displacement",
    values="Participants",
    title="Displacement status"
)

st.plotly_chart(fig_displacement, use_container_width=True)

st.subheader("Detailed data")
st.dataframe(filtered_df, use_container_width=True)
