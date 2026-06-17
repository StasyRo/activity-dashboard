import json
import re
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

GEOJSON_FILE = Path("rayons_en.geojson")


clean_name(original_name)
def clean_name(value):
    value = str(value).lower().strip()

    value = value.replace("’", "")
    value = value.replace("'", "")
    value = value.replace("`", "")
    value = value.replace("ʼ", "")

    words_to_remove = [
        "raion",
        "rayon",
        "district",
        "район"
    ]

    for word in words_to_remove:
        value = value.replace(word, "")

    value = re.sub(r"[^a-zа-яіїєґ0-9]+", "", value)

    return value

@st.cache_data
def load_geojson():
    if not GEOJSON_FILE.exists():
        st.error("GeoJSON file rayons_en.geojson was not found.")
        st.stop()

    with open(GEOJSON_FILE, "r", encoding="utf-8-sig") as file:
        raw_text = file.read()

    st.write("GeoJSON file size:", len(raw_text), "characters")
    st.write("First 500 characters of GeoJSON file:")
    st.code(raw_text[:500])

    try:
        geojson = json.loads(raw_text)
    except json.JSONDecodeError as e:
        st.error("This file is not valid JSON / GeoJSON.")
        st.write("JSON error:")
        st.code(str(e))
        st.stop()

    if "features" not in geojson:
        st.error("This file is JSON, but not GeoJSON FeatureCollection. No 'features' key found.")
        st.write("Top-level keys:")
        st.write(list(geojson.keys()))
        st.stop()

    for feature in geojson["features"]:
        props = feature.get("properties", {})

        original_name = (
            props.get("Rayon")
            or props.get("rayon")
            or props.get("Rayon_name")
            or props.get("rayon_name")
            or props.get("NAME_2")
            or props.get("Name")
            or props.get("name")
            or props.get("shapeName")
            or props.get("ADM2_EN")
            or props.get("ADM2_NAME")
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


# Participants by rayon from Excel
rayon_summary = (
    base_filtered_df.groupby("Rayon_clean", dropna=False)
    .agg(
        Participants=("Rayon_clean", "size"),
        Rayon_excel=("Rayon", "first")
    )
    .reset_index()
)

rayon_summary["Rayon_clean"] = rayon_summary["Rayon_clean"].astype(str)
rayon_summary["Rayon_excel"] = rayon_summary["Rayon_excel"].astype(str)


# Merge GeoJSON rayons with Excel participants
map_df = geo_rayons_df.merge(
    rayon_summary,
    on="Rayon_clean",
    how="left"
)

map_df["Participants"] = map_df["Participants"].fillna(0).astype(int)

# Hover name:
# if rayon exists in Excel, show Excel name;
# if not, show map name.
map_df["Hover rayon"] = map_df["Rayon_excel"].fillna(map_df["Rayon_name"])
map_df["Hover rayon"] = map_df["Hover rayon"].replace("nan", pd.NA)
map_df["Hover rayon"] = map_df["Hover rayon"].fillna(map_df["Rayon_name"])
map_df["Hover rayon"] = map_df["Hover rayon"].astype(str)


# Map
st.subheader("Ukraine map by rayon")
st.caption("Click on a rayon to filter all charts below.")

if st.session_state.selected_rayon_name:
    st.info(f"Selected rayon: {st.session_state.selected_rayon_name}")

    if st.button("Clear rayon selection"):
        st.session_state.selected_rayon_clean = None
        st.session_state.selected_rayon_name = None
        st.rerun()


max_participants = max(1, int(map_df["Participants"].max()))

fig_map = px.choropleth(
    map_df,
    geojson=geojson,
    locations="Rayon_clean",
    featureidkey="properties.rayon_clean",
    color="Participants",
    custom_data=["Rayon_clean", "Hover rayon", "Participants"],
    color_continuous_scale=[
        [0.0, "#fff7ed"],
        [0.5, "#fdba74"],
        [1.0, "#fb923c"]
    ],
    range_color=(0, max_participants)
)

fig_map.update_traces(
    marker_line_color="white",
    marker_line_width=0.6,
    hovertemplate="<b>%{customdata[1]}</b><br>Participants: %{customdata[2]}<extra></extra>"
)

fig_map.update_geos(
    fitbounds="locations",
    visible=False,
    showcountries=False,
    showcoastlines=False,
    showframe=False,
    bgcolor="rgba(0,0,0,0)",
    projection_type="mercator"
)

fig_map.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    height=700,
    coloraxis_colorbar_title="Participants"
)

map_event = st.plotly_chart(
    fig_map,
    key="ukraine_rayon_map",
    on_select="rerun",
    selection_mode="points",
    use_container_width=True
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
st.dataframe(
    filtered_df.drop(columns=["Rayon_clean"]),
    use_container_width=True
)

with st.expander("Technical check"):
    st.write("Total rows in file:", len(df))
    st.write("Rows after filters:", len(filtered_df))
    st.write("Selected rayon:", st.session_state.selected_rayon_name)
    st.write("Columns:", list(df.columns))

    st.subheader("Rayon matching check")

    excel_rayons = (
        df[["Rayon", "Rayon_clean"]]
        .drop_duplicates()
        .sort_values("Rayon")
    )

    map_rayons = (
        map_df[["Rayon_name", "Hover rayon", "Rayon_clean", "Participants"]]
        .drop_duplicates()
        .sort_values("Hover rayon")
    )

    st.write("Rayons from Excel:")
    st.dataframe(excel_rayons, use_container_width=True)

    st.write("Rayons from map:")
    st.dataframe(map_rayons, use_container_width=True)
