import json
import re
import urllib.request
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

GEOJSON_URL = (
    "https://raw.githubusercontent.com/slawomirmatuszak/"
    "ukrainian_geodata/main/rayony.geojson"
)


def clean_name(value):
    value = str(value).lower().strip()
    value = value.replace("’", "").replace("'", "").replace("`", "").replace("ʼ", "")
    value = re.sub(r"\b(raion|rayon|district)\b", "", value)
    value = re.sub(r"[^a-zа-яіїєґ0-9]+", "", value)
    return value


@st.cache_data
def load_geojson():
    with urllib.request.urlopen(GEOJSON_URL) as response:
        geojson = json.load(response)

    for feature in geojson["features"]:
        props = feature["properties"]

        original_name = (
            props.get("name")
            or props.get("NAME_2")
            or props.get("shapeName")
            or props.get("rayon")
            or props.get("Rayon")
            or ""
        )

        feature["properties"]["rayon_name"] = original_name
        feature["properties"]["rayon_clean"] = clean_name(original_name)

    return geojson


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

    for col in required_columns:
        data[col] = data[col].fillna("Not specified").astype(str).str.strip()

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Rayon_clean"] = data["Rayon"].apply(clean_name)

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

    st.plotly_chart(fig, width="stretch")


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

    st.plotly_chart(fig, width="stretch")


df = load_data()
geojson = load_geojson()

if "selected_rayon_clean" not in st.session_state:
    st.session_state.selected_rayon_clean = None

if "selected_rayon_name" not in st.session_state:
    st.session_state.selected_rayon_name = None


# Sidebar filters
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


# First filter without map rayon
base_filtered_df = df[
    df["Donor number"].isin(selected_donors) &
    df["Office"].isin(selected_offices) &
    df["Oblast"].isin(selected_oblasts) &
    df["Activity"].isin(selected_activities) &
    df["Gender"].isin(selected_gender) &
    df["Disability"].isin(selected_disability) &
    df["Displacement"].isin(selected_displacement)
]


# Prepare all rayons from GeoJSON
geo_rayons = []

for feature in geojson["features"]:
    geo_rayons.append({
        "Rayon_clean": feature["properties"].get("rayon_clean", ""),
        "Rayon_name": feature["properties"].get("rayon_name", "")
    })

geo_rayons_df = pd.DataFrame(geo_rayons).drop_duplicates()


# Participants by rayon
rayon_summary = (
    base_filtered_df.groupby("Rayon_clean", dropna=False)
    .size()
    .reset_index(name="Participants")
)

map_df = geo_rayons_df.merge(
    rayon_summary,
    on="Rayon_clean",
    how="left"
)

map_df["Participants"] = map_df["Participants"].fillna(0).astype(int)


st.subheader("Ukraine map by rayon")
st.caption("Click on a rayon to filter all charts below.")

if st.session_state.selected_rayon_name:
    st.info(f"Selected rayon: {st.session_state.selected_rayon_name}")

    if st.button("Clear rayon selection"):
        st.session_state.selected_rayon_clean = None
        st.session_state.selected_rayon_name = None
        st.rerun()


fig_map = px.choropleth_mapbox(
    map_df,
    geojson=geojson,
    locations="Rayon_clean",
    featureidkey="properties.rayon_clean",
    color="Participants",
    hover_name="Rayon_name",
    hover_data={
        "Participants": True,
        "Rayon_clean": False
    },
    custom_data=["Rayon_clean", "Rayon_name"],
    mapbox_style="carto-positron",
    center={
        "lat": 48.7,
        "lon": 31.2
    },
    zoom=4.8,
    opacity=0.65
)

fig_map.update_layout(
    margin={
        "r": 0,
        "t": 0,
        "l": 0,
        "b": 0
    },
    height=650,
    clickmode="event+select"
)

map_event = st.plotly_chart(
    fig_map,
    key="ukraine_rayon_map",
    on_select="rerun",
    selection_mode="points",
    width="stretch"
)

try:
    selected_points = map_event.selection.points

    if selected_points:
        custom_data = selected_points[0].get("customdata", [])

        if custom_data:
            st.session_state.selected_rayon_clean = custom_data[0]
            st.session_state.selected_rayon_name = custom_data[1]
            st.rerun()

except Exception:
    pass


# Apply rayon selection from map
filtered_df = base_filtered_df.copy()

if st.session_state.selected_rayon_clean:
    filtered_df = filtered_df[
        filtered_df["Rayon_clean"] == st.session_state.selected_rayon_clean
    ]


st.divider()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total participants", len(filtered_df))
col2.metric("Donors", filtered_df["Donor number"].nunique())
col3.metric("Activities", filtered_df["Activity"].nunique())
col4.metric("Hromadas", filtered_df["Hromada"].nunique())

st.divider()

if filtered_df.empty:
    st.warning("No data for selected filters.")
    st.stop()


make_bar(filtered_df, "Donor number", "Participants by donor")
make_bar(filtered_df, "Activity", "Participants by activity")
make_bar(filtered_df, "Oblast", "Participants by oblast")
make_bar(filtered_df, "Rayon", "Participants by rayon")
make_bar(filtered_df, "Hromada", "Participants by hromada")

make_pie(filtered_df, "Gender", "Gender breakdown")
make_pie(filtered_df, "Displacement", "Displacement status")
make_pie(filtered_df, "Disability", "Disability status")

st.subheader("Detailed data")
st.dataframe(filtered_df.drop(columns=["Rayon_clean"]), width="stretch")

with st.expander("Technical check"):
    st.write("Total rows in file:", len(df))
    st.write("Rows after filters:", len(filtered_df))
    st.write("Selected rayon:", st.session_state.selected_rayon_name)
    st.write("Columns:", list(df.columns))
