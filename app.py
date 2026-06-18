from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Activity Dashboard",
    page_icon="📊",
    layout="wide"
)

DATA_FILE = Path("Data.xlsx")
GEOJSON_FILE = Path("rayons_en.geojson")

CHART_COLOR = "#F4C21A"


st.markdown(
    """
    <style>
    .main-title {
        font-size: 34px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0px;
    }

    .main-subtitle {
        font-size: 15px;
        color: #6b7280;
        margin-bottom: 22px;
    }

    .metric-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 22px 18px;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
        min-height: 135px;
        margin-bottom: 14px;
    }

    .metric-icon {
        font-size: 38px;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 34px;
        font-weight: 800;
        color: #111827;
        line-height: 1.1;
    }

    .metric-title {
        font-size: 15px;
        font-weight: 600;
        color: #374151;
        margin-top: 8px;
    }

    .filter-title {
        font-size: 22px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 4px;
    }

    .filter-subtitle {
        font-size: 13px;
        color: #6b7280;
        margin-bottom: 16px;
    }

    .map-placeholder {
        background: #fff7ed;
        border: 1px dashed #fb923c;
        border-radius: 18px;
        padding: 60px 24px;
        text-align: center;
        color: #9a3412;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .map-placeholder-icon {
        font-size: 52px;
        margin-bottom: 10px;
    }

    .map-placeholder-title {
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .map-placeholder-text {
        font-size: 15px;
        color: #9a3412;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    '<div class="main-title">📊 Activity Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">Overview of clients by donor, location and activity</div>',
    unsafe_allow_html=True
)


@st.cache_data
def load_data():
    if not DATA_FILE.exists():
        st.error("Excel file Data.xlsx was not found.")
        st.stop()

    data = pd.read_excel(DATA_FILE, sheet_name="TotalF", engine="openpyxl")
    data.columns = data.columns.str.strip()

    required_columns = [
        "Date",
        "Oblast",
        "Donor number",
        "Gender",
        "Displacement",
        "Disability",
        "Rayon",
        "ActDis",
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
        "Donor number",
        "Gender",
        "Displacement",
        "Disability",
        "Rayon",
        "ActDis",
        "Activity"
    ]

    for col in text_columns:
        data[col] = (
            data[col]
            .fillna("Not specified")
            .astype(str)
            .str.strip()
            .str.replace("_", " ", regex=False)
        )

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

    return data

def ring_area(ring):
area = 0.0

for i in range(len(ring) - 1):
    x1, y1 = ring[i][0], ring[i][1]
    x2, y2 = ring[i + 1][0], ring[i + 1][1]
    area += (x1 * y2) - (x2 * y1)

return area / 2

def ensure_closed_ring(ring):
if ring and ring[0] != ring[-1]:
ring = ring + [ring[0]]

return ring

def fix_polygon_rings(rings):
if not rings:
return rings

fixed_rings = []

exterior_ring = ensure_closed_ring(rings[0])

if ring_area(exterior_ring) < 0:
    exterior_ring = list(reversed(exterior_ring))

fixed_rings.append(exterior_ring)

for hole in rings[1:]:
    hole = ensure_closed_ring(hole)

    if ring_area(hole) > 0:
        hole = list(reversed(hole))

    fixed_rings.append(hole)

return fixed_rings

def fix_geojson_winding(geojson):
for feature in geojson["features"]:
geometry = feature.get("geometry")

    if not geometry:
        continue

    if geometry["type"] == "Polygon":
        geometry["coordinates"] = fix_polygon_rings(
            geometry["coordinates"]
        )

    elif geometry["type"] == "MultiPolygon":
        geometry["coordinates"] = [
            fix_polygon_rings(polygon)
            for polygon in geometry["coordinates"]
        ]

return geojson

@st.cache_data
def load_geojson():
    if not GEOJSON_FILE.exists():
        st.error(f"GeoJSON file {GEOJSON_FILE} was not found.")
        st.stop()

    with open(GEOJSON_FILE, "r", encoding="utf-8-sig") as file:
        raw_text = file.read().strip()

    if not raw_text:
        st.error(f"The file {GEOJSON_FILE} is empty.")
        st.stop()

    if raw_text.startswith("<"):
        st.error(f"The file {GEOJSON_FILE} looks like an HTML page, not a GeoJSON file.")
        st.write("You probably uploaded a GitHub page instead of the raw GeoJSON file.")
        st.stop()

    try:
        geojson_raw = json.loads(raw_text)
    except json.JSONDecodeError as error:
        st.error(f"The file {GEOJSON_FILE} is not valid JSON / GeoJSON.")
        st.write(f"JSON error: line {error.lineno}, column {error.colno}")
        st.write("First characters of the file:")
        st.code(raw_text[:300])
        st.stop()

    if isinstance(geojson_raw, dict) and "features" in geojson_raw:
        geojson = geojson_raw
    elif isinstance(geojson_raw, list):
        geojson = {
            "type": "FeatureCollection",
            "features": geojson_raw
        }
    elif isinstance(geojson_raw, dict) and geojson_raw.get("type") == "Feature":
        geojson = {
            "type": "FeatureCollection",
            "features": [geojson_raw]
        }
    else:
        st.error("The map file is not a valid GeoJSON FeatureCollection.")
        st.write("Expected structure:")
        st.code('{"type": "FeatureCollection", "features": [...]}')
        st.write("Your file has this structure:")
        st.write(geojson_raw.keys() if isinstance(geojson_raw, dict) else type(geojson_raw))
        st.stop()

    if not geojson.get("features"):
        st.error("GeoJSON file has no features.")
        st.stop()

    for feature in geojson["features"]:
        props = feature.get("properties", {})

        original_name = (
            props.get("Rayon")
            or props.get("rayon")
            or props.get("rayon_name")
            or props.get("name")
            or props.get("Name")
            or props.get("NAME_2")
            or props.get("shapeName")
            or props.get("ADM2_EN")
            or props.get("ADM2_NAME")
            or ""
        )

        feature["properties"]["rayon_name"] = str(original_name).strip()
        feature["properties"]["rayon_key"] = str(original_name).strip().lower()

    return geojson


def build_map_data(dataframe, geojson):
    rayon_summary = (
        dataframe.groupby("Rayon", dropna=False)
        .size()
        .reset_index(name="Clients")
    )

    rayon_summary["Rayon"] = rayon_summary["Rayon"].astype(str).str.strip()
    rayon_summary["rayon_key"] = rayon_summary["Rayon"].str.lower()

    geo_records = []
    for feature in geojson["features"]:
        geo_records.append({
            "rayon_key": feature["properties"].get("rayon_key", ""),
            "rayon_name": feature["properties"].get("rayon_name", "")
        })

    geo_df = pd.DataFrame(geo_records).drop_duplicates()

    map_df = geo_df.merge(
        rayon_summary,
        on="rayon_key",
        how="left"
    )

    map_df["Clients"] = map_df["Clients"].fillna(0).astype(int)
    map_df["Rayon"] = map_df["Rayon"].fillna(map_df["rayon_name"])

    return map_df


def show_map(dataframe, geojson):
    map_df = build_map_data(dataframe, geojson)

    active_df = map_df[map_df["Clients"] > 0].copy()

    fig = go.Figure()

    fig.add_trace( 
        go.Choropleth( 
            geojson=geojson, 
            locations=map_df["rayon_key"], 
            z=[0] * len(map_df), 
            featureidkey="properties.rayon_key", 
            colorscale=[ 
                [0, "rgba(255,255,255,0)"], 
                [1, "rgba(255,255,255,0)"] 
            ], 
            marker_line_color="#9ca3af", 
            marker_line_width=0.5, 
            showscale=False, 
            hoverinfo="skip" 
        ) 
    ) 
    
    if not active_df.empty: 
        max_clients = max(1, int(active_df["Clients"].max())) 
        
        fig.add_trace( 
            go.Choropleth( 
                geojson=geojson, 
                locations=active_df["rayon_key"], 
                z=active_df["Clients"], 
                featureidkey="properties.rayon_key", 
                colorscale=[ 
                    [0.0, "#fed7aa"], 
                    [0.5, "#fb923c"], 
                    [1.0, "#c2410c"] 
                ], 
                zmin=0, 
                zmax=max_clients, 
                marker_line_color="white", 
                marker_line_width=0.8, 
                colorbar_title="Clients", 
                text=active_df["Rayon"], 
                hovertemplate="<b>%{text}</b><br>Clients: %{z}<extra></extra>" 
            ) 
        ) 
        
        fig.update_geos( 
            fitbounds="geojson", 
            visible=False, 
            showcountries=False, 
            showcoastlines=False, 
            showframe=False, 
            bgcolor="rgba(0,0,0,0)" 
        ) 
        
        fig.update_layout( 
            height=700, 
            margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
            paper_bgcolor="white", 
            plot_bgcolor="white" 
        ) 
        
        st.plotly_chart(fig, use_container_width=True)


def get_options(dataframe, column):
    return sorted(dataframe[column].dropna().astype(str).unique().tolist())


def render_card(icon, title, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-value">{value:,}</div>
            <div class="metric-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def count_gender(dataframe, gender_value):
    return dataframe[dataframe["Gender"] == gender_value].shape[0]


def count_displacement_exact(dataframe, values):
    return dataframe[dataframe["Displacement"].isin(values)].shape[0]


def count_disability(dataframe):
    no_disability_values = [
        "No",
        "no",
        "None",
        "none",
        "Not specified",
        ""
    ]

    return dataframe[~dataframe["Disability"].isin(no_disability_values)].shape[0]


def make_bar(dataframe, group_column, title, top_n=None):
    summary = (
        dataframe.groupby(group_column, dropna=False)
        .size()
        .reset_index(name="Clients")
        .sort_values("Clients", ascending=False)
    )

    if top_n is not None:
        summary = summary.head(top_n)

    summary[group_column] = summary[group_column].astype(str)

    fig = px.bar(
        summary,
        x=group_column,
        y="Clients",
        text="Clients",
        title=title,
        color_discrete_sequence=[CHART_COLOR]
    )

    fig.update_traces(
        marker_line_color="#D4A514",
        marker_line_width=0.8,
        textfont=dict(color="black", size=13)
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, color="black")
        ),
        font=dict(color="black"),
        xaxis_title="",
        yaxis_title="Clients",
        margin=dict(l=20, r=20, t=60, b=80)
    )

    fig.update_xaxes(
        tickfont=dict(color="black"),
        tickangle=-35
    )

    fig.update_yaxes(
        tickfont=dict(color="black")
    )

    st.plotly_chart(fig, use_container_width=True)


df = load_data()
geojson = load_geojson()


st.sidebar.markdown(
    '<div class="filter-title">Filters</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown(
    '<div class="filter-subtitle">Use filters to update all figures and charts.</div>',
    unsafe_allow_html=True
)

valid_dates = df["Date"].dropna()


with st.sidebar.container(border=True):
    st.markdown("### 📅 Date period")

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        start_date = st.date_input(
            "Start date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )

        end_date = st.date_input(
            "End date",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    else:
        start_date = None
        end_date = None
        st.info("No valid dates found.")


with st.sidebar.container(border=True):
    st.markdown("### 📍 Location")

    oblasts = get_options(df, "Oblast")
    rayons = get_options(df, "Rayon")

    selected_oblasts = st.multiselect(
        "Oblast",
        oblasts,
        default=oblasts
    )

    selected_rayons = st.multiselect(
        "Rayon",
        rayons,
        default=rayons
    )


with st.sidebar.container(border=True):
    st.markdown("### 💰 Donor")

    donors = get_options(df, "Donor number")

    selected_donors = st.multiselect(
        "Donor number",
        donors,
        default=donors,
        label_visibility="collapsed"
    )

    st.markdown("### 📋 Activity")

    activities = get_options(df, "Activity")

    selected_activities = st.multiselect(
        "Activity",
        activities,
        default=activities,
        label_visibility="collapsed"
    )


with st.sidebar.container(border=True):
    st.markdown("### 👥 Participant profile")

    gender = get_options(df, "Gender")
    displacement = get_options(df, "Displacement")
    disability = get_options(df, "Disability")
    actdis = get_options(df, "ActDis")

    selected_gender = st.multiselect(
        "Gender",
        gender,
        default=gender
    )

    selected_displacement = st.multiselect(
        "Displacement",
        displacement,
        default=displacement
    )

    selected_disability = st.multiselect(
        "Disability",
        disability,
        default=disability
    )

    selected_actdis = st.multiselect(
        "ActDis",
        actdis,
        default=actdis
    )


filtered_df = df[
    df["Oblast"].isin(selected_oblasts) &
    df["Rayon"].isin(selected_rayons) &
    df["Donor number"].isin(selected_donors) &
    df["Activity"].isin(selected_activities) &
    df["Gender"].isin(selected_gender) &
    df["Displacement"].isin(selected_displacement) &
    df["Disability"].isin(selected_disability) &
    df["ActDis"].isin(selected_actdis)
]

if start_date is not None and end_date is not None:
    if start_date > end_date:
        st.error("Start date cannot be later than end date.")
        st.stop()

    filtered_df = filtered_df[
        (filtered_df["Date"].dt.date >= start_date) &
        (filtered_df["Date"].dt.date <= end_date)
    ]


total_count = len(filtered_df)
female_count = count_gender(filtered_df, "female")
male_count = count_gender(filtered_df, "male")

local_count = count_displacement_exact(
    filtered_df,
    ["local population"]
)

idp_count = count_displacement_exact(
    filtered_df,
    ["displaced person"]
)

returnee_count = count_displacement_exact(
    filtered_df,
    ["returnee"]
)

pwd_count = count_disability(filtered_df)


st.subheader("Key figures")

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    render_card("👥", "Total Clients", total_count)

with row1_col2:
    render_card("👩", "Women", female_count)

with row1_col3:
    render_card("👨", "Men", male_count)


row2_col1, row2_col2, row2_col3 = st.columns(3)

with row2_col1:
    render_card("🏠", "Local people", local_count)

with row2_col2:
    render_card("🧳", "IDPs", idp_count)

with row2_col3:
    render_card("↩️", "Returnees", returnee_count)


row3_col1, row3_col2, row3_col3 = st.columns(3)

with row3_col1:
    st.empty()

with row3_col2:
    render_card("♿", "People with disabilities", pwd_count)

with row3_col3:
    st.empty()


row4_col1, row4_col2 = st.columns(2)

with row4_col1:
    render_card("💰", "Donors", filtered_df["Donor number"].nunique())

with row4_col2:
    render_card("📋", "Activities", filtered_df["Activity"].nunique())


st.divider()

if filtered_df.empty:
    st.warning("No data for selected filters.")
    st.stop()


tab_map, tab_overview, tab_location, tab_profile = st.tabs([
    "Map",
    "Overview",
    "Location",
    "Profile",
])


with tab_map:
    st.subheader("Map of Ukraine by rayon")
    st.caption("Rayons with more clients are shown in darker orange.")

    show_map(filtered_df, geojson)


with tab_overview:
    make_bar(filtered_df, "Donor number", "Clients by donor")
    make_bar(filtered_df, "Activity", "Top activities by clients", top_n=20)


with tab_location:
    make_bar(filtered_df, "Oblast", "Clients by oblast")
    make_bar(filtered_df, "Rayon", "Clients by rayon", top_n=25)


with tab_profile:
    make_bar(filtered_df, "Gender", "Gender breakdown")
    make_bar(filtered_df, "Displacement", "Displacement status")
    make_bar(filtered_df, "Disability", "Disability status")
    make_bar(filtered_df, "ActDis", "Clients by age/disability category")
