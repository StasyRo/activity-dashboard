from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Activity Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Activity Dashboard")
st.caption("Overview of participants by donor, location and activity")

DATA_FILE = Path("Data.xlsx")


@st.cache_data
def load_data():
    if not DATA_FILE.exists():
        st.error("Excel file Data.xlsx was not found.")
        st.stop()

    data = pd.read_excel(DATA_FILE, engine="openpyxl")
    data.columns = data.columns.str.strip()

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

    missing_columns = [col for col in required_columns if col not in data.columns]

    if missing_columns:
        st.error("Missing required columns:")
        st.write(missing_columns)

        st.subheader("Columns found in your Excel:")
        st.write(list(data.columns))
        st.stop()

    text_columns = [
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

    for col in text_columns:
        data[col] = data[col].fillna("Not specified").astype(str).str.strip()

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

    return data


def get_options(dataframe, column):
    return sorted(dataframe[column].dropna().astype(str).unique().tolist())


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

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Participants"
    )

    st.plotly_chart(fig, use_container_width=True)


def make_horizontal_bar(dataframe, group_column, title, top_n=20):
    summary = (
        dataframe.groupby(group_column, dropna=False)
        .size()
        .reset_index(name="Participants")
        .sort_values("Participants", ascending=False)
        .head(top_n)
    )

    summary[group_column] = summary[group_column].astype(str)

    fig = px.bar(
        summary,
        x="Participants",
        y=group_column,
        text="Participants",
        title=title,
        orientation="h"
    )

    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Participants",
        yaxis_title=""
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


df = load_data()

st.sidebar.header("Filters")

donors = get_options(df, "Donor number")
offices = get_options(df, "Office")
oblasts = get_options(df, "Oblast")
rayons = get_options(df, "Rayon")
hromadas = get_options(df, "Hromada")
activities = get_options(df, "Activity")
gender = get_options(df, "Gender")
disability = get_options(df, "Disability")
displacement = get_options(df, "Displacement")

selected_donors = st.sidebar.multiselect("Donor", donors, default=donors)
selected_offices = st.sidebar.multiselect("Office", offices, default=offices)
selected_oblasts = st.sidebar.multiselect("Oblast", oblasts, default=oblasts)
selected_rayons = st.sidebar.multiselect("Rayon", rayons, default=rayons)
selected_hromadas = st.sidebar.multiselect("Hromada", hromadas, default=hromadas)
selected_activities = st.sidebar.multiselect("Activity", activities, default=activities)
selected_gender = st.sidebar.multiselect("Gender", gender, default=gender)
selected_disability = st.sidebar.multiselect("Disability", disability, default=disability)
selected_displacement = st.sidebar.multiselect("Displacement", displacement, default=displacement)

filtered_df = df[
    df["Donor number"].isin(selected_donors) &
    df["Office"].isin(selected_offices) &
    df["Oblast"].isin(selected_oblasts) &
    df["Rayon"].isin(selected_rayons) &
    df["Hromada"].isin(selected_hromadas) &
    df["Activity"].isin(selected_activities) &
    df["Gender"].isin(selected_gender) &
    df["Disability"].isin(selected_disability) &
    df["Displacement"].isin(selected_displacement)
]

valid_dates = filtered_df["Date"].dropna()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range

        filtered_df = filtered_df[
            (filtered_df["Date"].dt.date >= start_date) &
            (filtered_df["Date"].dt.date <= end_date)
        ]


st.divider()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total participants", len(filtered_df))
col2.metric("Donors", filtered_df["Donor number"].nunique())
col3.metric("Activities", filtered_df["Activity"].nunique())
col4.metric("Hromadas", filtered_df["Hromada"].nunique())

col5, col6, col7, col8 = st.columns(4)

col5.metric("Oblasts", filtered_df["Oblast"].nunique())
col6.metric("Rayons", filtered_df["Rayon"].nunique())
col7.metric("Offices", filtered_df["Office"].nunique())
col8.metric("With disability", len(filtered_df[filtered_df["Disability"].str.lower() != "no"]))

st.divider()

if filtered_df.empty:
    st.warning("No data for selected filters.")
    st.stop()


tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Location",
    "Profile",
    "Detailed data"
])

with tab1:
    make_bar(filtered_df, "Donor number", "Participants by donor")
    make_horizontal_bar(filtered_df, "Activity", "Top activities by participants", top_n=20)
    make_bar(filtered_df, "Office", "Participants by office")

with tab2:
    make_bar(filtered_df, "Oblast", "Participants by oblast")
    make_horizontal_bar(filtered_df, "Rayon", "Participants by rayon", top_n=25)
    make_horizontal_bar(filtered_df, "Hromada", "Top hromadas by participants", top_n=25)

with tab3:
    make_pie(filtered_df, "Gender", "Gender breakdown")
    make_pie(filtered_df, "Displacement", "Displacement status")
    make_pie(filtered_df, "Disability", "Disability status")
    make_bar(filtered_df, "ActDis", "Participants by age/disability category")

with tab4:
    st.subheader("Detailed data")
    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="filtered_activity_data.csv",
        mime="text/csv"
    )

with st.expander("Technical check"):
    st.write("Total rows in file:", len(df))
    st.write("Rows after filters:", len(filtered_df))
    st.write("Columns:", list(df.columns))
