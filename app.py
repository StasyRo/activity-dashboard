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
SHEET_NAME = "TotalF"

CHART_COLOR = "#F4C21A"
CHART_BORDER_COLOR = "#D4A514"

ORANGE_SCALE = [
    [0.0, "#fed7aa"],
    [0.5, "#fb923c"],
    [1.0, "#c2410c"]
]


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }

    .hero-card {
        background: linear-gradient(135deg, #fff7ed 0%, #ffffff 58%, #fef3c7 100%);
        border: 1px solid #fed7aa;
        border-radius: 22px;
        padding: 18px 24px;
        margin-bottom: 18px;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.07);
    }

    .main-title {
        font-size: 32px;
        font-weight: 900;
        color: #111827;
        margin-bottom: 2px;
        letter-spacing: -0.03em;
    }

    .main-subtitle {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 0px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 850;
        color: #111827;
        margin-top: 6px;
        margin-bottom: 10px;
    }

    .group-title {
        font-size: 14px;
        font-weight: 800;
        color: #374151;
        margin-top: 10px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #F4C21A;
        border-radius: 16px;
        padding: 11px 12px;
        text-align: left;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.055);
        min-height: 78px;
        margin-bottom: 8px;
    }

    .metric-top {
        display: flex;
        align-items: center;
        gap: 7px;
        margin-bottom: 5px;
    }

    .metric-icon {
        font-size: 19px;
        line-height: 1;
    }

    .metric-title {
        font-size: 11.5px;
        font-weight: 750;
        color: #6b7280;
        line-height: 1.15;
    }

    .metric-value {
        font-size: 23px;
        font-weight: 900;
        color: #111827;
        line-height: 1.05;
        letter-spacing: -0.03em;
    }

    .small-note {
        color: #6b7280;
        font-size: 13px;
        margin-top: -4px;
        margin-bottom: 14px;
    }

    .filter-title {
        font-size: 23px;
        font-weight: 900;
        color: #111827;
        margin-bottom: 4px;
    }

    .filter-subtitle {
        font-size: 13px;
        color: #6b7280;
        margin-bottom: 16px;
    }

    .active-filter-box {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 16px;
        padding: 12px 14px;
        color: #92400e;
        margin-bottom: 16px;
        font-size: 14px;
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

    div[data-testid="stSidebar"] {
        background: #fafafa;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div class="hero-card">
        <div class="main-title">📊 Activity Dashboard</div>
        <div class="main-subtitle">
            Overview of clients, received EUR amount, donors, locations and activities
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


@st.cache_data
def load_data():
    if not DATA_FILE.exists():
        st.error("Excel file Data.xlsx was not found.")
        st.stop()

    data = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
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
        "Activity",
        "Receive Amount EUR"
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

    data["Receive Amount EUR"] = pd.to_numeric(
        data["Receive Amount EUR"],
        errors="coerce"
    ).fillna(0)

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

    if ring_area(exterior_ring) > 0:
        exterior_ring = list(reversed(exterior_ring))

    fixed_rings.append(exterior_ring)

    for hole in rings[1:]:
        hole = ensure_closed_ring(hole)

        if ring_area(hole) < 0:
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
        return None

    with open(GEOJSON_FILE, "r", encoding="utf-8-sig") as file:
        raw_text = file.read().strip()

    if not raw_text:
        return None

    if raw_text.startswith("<"):
        return None

    try:
        geojson_raw = json.loads(raw_text)
    except json.JSONDecodeError:
        return None

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
        return None

    if not geojson.get("features"):
        return None

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

    geojson = fix_geojson_winding(geojson)

    return geojson


def get_options(dataframe, column):
    return sorted(dataframe[column].dropna().astype(str).unique().tolist())


def format_number(value):
    return f"{value:,.0f}"


def format_eur(value):
    return f"€{value:,.0f}"


def render_card(icon, title, value):
    if isinstance(value, (int, float)):
        display_value = format_number(value)
    else:
        display_value = str(value)

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-icon">{icon}</div>
                <div class="metric-title">{title}</div>
            </div>
            <div class="metric-value">{display_value}</div>
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


def make_bar(dataframe, group_column, title, value_column=None, top_n=None, y_title=None):
    if value_column:
        summary = (
            dataframe.groupby(group_column, dropna=False)[value_column]
            .sum()
            .reset_index(name="Value")
            .sort_values("Value", ascending=False)
        )
        text_template = "€%{y:,.0f}"
        y_axis_title = y_title or "EUR"
        hover_template = "<b>%{x}</b><br>EUR: €%{y:,.0f}<extra></extra>"
    else:
        summary = (
            dataframe.groupby(group_column, dropna=False)
            .size()
            .reset_index(name="Value")
            .sort_values("Value", ascending=False)
        )
        text_template = "%{y:,.0f}"
        y_axis_title = y_title or "Clients"
        hover_template = "<b>%{x}</b><br>Clients: %{y:,.0f}<extra></extra>"

    if top_n is not None:
        summary = summary.head(top_n)

    summary[group_column] = summary[group_column].astype(str)

    max_value = summary["Value"].max() if not summary.empty else 0
    y_range_max = max_value * 1.18 if max_value > 0 else 1

    fig = px.bar(
        summary,
        x=group_column,
        y="Value",
        text="Value",
        title=title,
        color_discrete_sequence=[CHART_COLOR]
    )

    fig.update_traces(
        marker_line_color=CHART_BORDER_COLOR,
        marker_line_width=0.8,
        texttemplate=text_template,
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color="black", size=13),
        hovertemplate=hover_template
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, color="black")
        ),
        font=dict(color="black"),
        xaxis_title="",
        yaxis_title=y_axis_title,
        margin=dict(l=20, r=35, t=60, b=90),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_color="black"
        ),
        uniformtext_minsize=12,
        uniformtext_mode="show"
    )

    fig.update_xaxes(
        tickfont=dict(color="black"),
        tickangle=-35,
        showgrid=False
    )

    fig.update_yaxes(
        tickfont=dict(color="black"),
        gridcolor="#f3f4f6",
        range=[0, y_range_max]
    )

    st.plotly_chart(fig, use_container_width=True)


def make_horizontal_bar(dataframe, group_column, title, value_column=None, top_n=15, x_title=None):
    if value_column:
        summary = (
            dataframe.groupby(group_column, dropna=False)[value_column]
            .sum()
            .reset_index(name="Value")
            .sort_values("Value", ascending=False)
            .head(top_n)
        )
        text_template = "€%{x:,.0f}"
        x_axis_title = x_title or "EUR"
        hover_template = "<b>%{y}</b><br>EUR: €%{x:,.0f}<extra></extra>"
    else:
        summary = (
            dataframe.groupby(group_column, dropna=False)
            .size()
            .reset_index(name="Value")
            .sort_values("Value", ascending=False)
            .head(top_n)
        )
        text_template = "%{x:,.0f}"
        x_axis_title = x_title or "Clients"
        hover_template = "<b>%{y}</b><br>Clients: %{x:,.0f}<extra></extra>"

    summary[group_column] = summary[group_column].astype(str)

    max_value = summary["Value"].max() if not summary.empty else 0
    x_range_max = max_value * 1.18 if max_value > 0 else 1
    chart_height = max(430, 34 * len(summary) + 120)

    fig = px.bar(
        summary,
        x="Value",
        y=group_column,
        text="Value",
        title=title,
        orientation="h",
        color_discrete_sequence=[CHART_COLOR]
    )

    fig.update_traces(
        marker_line_color=CHART_BORDER_COLOR,
        marker_line_width=0.8,
        texttemplate=text_template,
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color="black", size=13),
        hovertemplate=hover_template
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, color="black")
        ),
        font=dict(color="black"),
        xaxis_title=x_axis_title,
        yaxis_title="",
        height=chart_height,
        margin=dict(l=20, r=95, t=60, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_color="black"
        ),
        uniformtext_minsize=12,
        uniformtext_mode="show"
    )

    fig.update_xaxes(
        tickfont=dict(color="black"),
        gridcolor="#f3f4f6",
        range=[0, x_range_max]
    )

    fig.update_yaxes(
        tickfont=dict(color="black"),
        categoryorder="total ascending"
    )

    st.plotly_chart(fig, use_container_width=True)


def build_map_data(dataframe, geojson):
    rayon_summary = (
        dataframe.groupby("Rayon", dropna=False)
        .agg(
            Clients=("Rayon", "size"),
            Amount_EUR=("Receive Amount EUR", "sum")
        )
        .reset_index()
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
    map_df["Amount_EUR"] = map_df["Amount_EUR"].fillna(0)
    map_df["Rayon"] = map_df["Rayon"].fillna(map_df["rayon_name"])

    return map_df


def show_map(dataframe, geojson):
    if geojson is None:
        st.markdown(
            """
            <div class="map-placeholder">
                <div class="map-placeholder-icon">🗺️</div>
                <div class="map-placeholder-title">Map file is not ready</div>
                <div class="map-placeholder-text">
                    Please check that rayons_en.geojson is a valid GeoJSON file.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

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
            marker_line_color="#d1d5db",
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
                colorscale=ORANGE_SCALE,
                zmin=1,
                zmax=max_clients,
                marker_line_color="white",
                marker_line_width=0.7,
                colorbar_title="Clients",
                text=active_df["Rayon"],
                customdata=active_df[["Amount_EUR"]],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Clients: %{z:,.0f}<br>"
                    "EUR: €%{customdata[0]:,.0f}"
                    "<extra></extra>"
                )
            )
        )

    fig.update_geos(
        visible=False,
        showcountries=False,
        showcoastlines=False,
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
        projection_type="mercator",
        lonaxis_range=[22, 41],
        lataxis_range=[44, 53]
    )

    fig.update_layout(
        height=720,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="white",
        plot_bgcolor="white",
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_color="black"
        )
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
    st.markdown("### 🗺️ Quick rayon focus")

    rayon_focus_options = ["All rayons"] + get_options(df, "Rayon")

    selected_rayon_focus = st.selectbox(
        "Focus rayon",
        rayon_focus_options,
        label_visibility="collapsed"
    )


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
    st.markdown("### 👥 Client profile")

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

if selected_rayon_focus != "All rayons":
    filtered_df = filtered_df[
        filtered_df["Rayon"] == selected_rayon_focus
    ]

if start_date is not None and end_date is not None:
    if start_date > end_date:
        st.error("Start date cannot be later than end date.")
        st.stop()

    filtered_df = filtered_df[
        (filtered_df["Date"].dt.date >= start_date) &
        (filtered_df["Date"].dt.date <= end_date)
    ]


if selected_rayon_focus != "All rayons":
    st.markdown(
        f"""
        <div class="active-filter-box">
            Active quick rayon filter: <b>{selected_rayon_focus}</b>
        </div>
        """,
        unsafe_allow_html=True
    )


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

total_eur = filtered_df["Receive Amount EUR"].sum()


st.markdown('<div class="section-title">Key figures</div>', unsafe_allow_html=True)

st.markdown('<div class="group-title">Impact summary</div>', unsafe_allow_html=True)

impact1, impact2 = st.columns(2)

with impact1:
    render_card("👥", "Total Clients", total_count)

with impact2:
    render_card("💶", "Total received EUR", format_eur(total_eur))


st.markdown('<div class="group-title">Client profile</div>', unsafe_allow_html=True)

profile1, profile2, profile3, profile4, profile5, profile6 = st.columns(6)

with profile1:
    render_card("👩", "Women", female_count)

with profile2:
    render_card("👨", "Men", male_count)

with profile3:
    render_card("🏠", "Local people", local_count)

with profile4:
    render_card("🧳", "IDPs", idp_count)

with profile5:
    render_card("↩️", "Returnees", returnee_count)

with profile6:
    render_card("♿", "People with disabilities", pwd_count)


st.markdown('<div class="group-title">Coverage</div>', unsafe_allow_html=True)

coverage1, coverage2, coverage3, coverage4 = st.columns(4)

with coverage1:
    render_card("💰", "Donors", filtered_df["Donor number"].nunique())

with coverage2:
    render_card("📋", "Activities", filtered_df["Activity"].nunique())

with coverage3:
    render_card("📍", "Oblasts", filtered_df["Oblast"].nunique())

with coverage4:
    render_card("🗺️", "Rayons", filtered_df["Rayon"].nunique())


st.divider()

if filtered_df.empty:
    st.warning("No data for selected filters.")
    st.stop()


tab_map, tab_overview, tab_money, tab_location, tab_profile = st.tabs([
    "Map",
    "Overview",
    "EUR analysis",
    "Location",
    "Profile"
])


with tab_map:
    st.markdown('<div class="section-title">Map of Ukraine by rayon</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="small-note">Rayons with more clients are shown in darker orange. Use “Quick rayon focus” in the sidebar to filter the whole dashboard by rayon.</div>',
        unsafe_allow_html=True
    )

    show_map(filtered_df, geojson)


with tab_overview:
    left_col, right_col = st.columns(2)

    with left_col:
        make_bar(filtered_df, "Donor number", "Clients by donor")

    with right_col:
        make_horizontal_bar(filtered_df, "Activity", "Top activities by clients", top_n=15)


with tab_money:
    left_col, right_col = st.columns(2)

    with left_col:
        make_bar(
            filtered_df,
            "Donor number",
            "Received EUR by donor",
            value_column="Receive Amount EUR",
            y_title="EUR"
        )

    with right_col:
        make_horizontal_bar(
            filtered_df,
            "Activity",
            "Received EUR by activity",
            value_column="Receive Amount EUR",
            top_n=15,
            x_title="EUR"
        )

    left_col2, right_col2 = st.columns(2)

    with left_col2:
        make_bar(
            filtered_df,
            "Oblast",
            "Received EUR by oblast",
            value_column="Receive Amount EUR",
            y_title="EUR"
        )

    with right_col2:
        make_horizontal_bar(
            filtered_df,
            "Rayon",
            "Received EUR by rayon",
            value_column="Receive Amount EUR",
            top_n=15,
            x_title="EUR"
        )


with tab_location:
    left_col, right_col = st.columns(2)

    with left_col:
        make_bar(filtered_df, "Oblast", "Clients by oblast")

    with right_col:
        make_horizontal_bar(filtered_df, "Rayon", "Clients by rayon", top_n=15)


with tab_profile:
    left_col, right_col = st.columns(2)

    with left_col:
        make_bar(filtered_df, "Gender", "Gender breakdown")
        make_bar(filtered_df, "Displacement", "Displacement status")

    with right_col:
        make_bar(filtered_df, "Disability", "Disability status")
        make_bar(filtered_df, "ActDis", "Clients by age/disability category")
