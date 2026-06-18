from pathlib import Path


import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Activity Dashboard",
    page_icon="📊",
    layout="wide"
)

DATA_FILE = Path("Data.xlsx")
CHART_COLOR = "#F4C21A"

PIE_COLORS = [
    "#F4C21A",
    "#F7CF4A",
    "#F9DB74",
    "#FBE7A0",
    "#FDF0C8",
    "#E5A50A",
    "#C98D08"
]


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

    .filter-section {
        font-size: 14px;
        font-weight: 700;
        color: #374151;
        margin-top: 16px;
        margin-bottom: 4px;
        padding-top: 10px;
        border-top: 1px solid #e5e7eb;
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


st.markdown('<div class="main-title">📊 Activity Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Overview of participants by donor, location and activity</div>',
    unsafe_allow_html=True
)


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
        data[col] = data[col].fillna("Not specified").astype(str).str.strip()

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

    return data


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
    gender_clean = (
        dataframe["Gender"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    return dataframe[
        gender_clean == gender_value.lower()
    ].shape[0]


def count_displacement(dataframe, keywords):
    displacement_clean = (
        dataframe["Displacement"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    pattern = "|".join(keywords)

    return dataframe[
        displacement_clean.str.contains(pattern, na=False)
    ].shape[0]


def count_disability(dataframe):
    disability_clean = (
        dataframe["Disability"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    no_disability_values = [
        "no",
        "none",
        "not specified",
        "",
        "nan"
    ]

    return dataframe[
        ~disability_clean.isin(no_disability_values)
    ].shape[0]


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
        title=title,
        color_discrete_sequence=[CHART_COLOR]
    )

    fig.update_traces(
        marker_line_color="#D4A514",
        marker_line_width=0.8
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Participants",
        title_font_size=20,
        margin=dict(l=20, r=20, t=60, b=20)
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
        orientation="h",
        color_discrete_sequence=[CHART_COLOR]
    )

    fig.update_traces(
        marker_line_color="#D4A514",
        marker_line_width=0.8
    )

    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Participants",
        yaxis_title="",
        title_font_size=20,
        margin=dict(l=20, r=20, t=60, b=20)
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
        title=title,
        color_discrete_sequence=PIE_COLORS
    )

    fig.update_traces(
        textinfo="percent+label",
        marker=dict(line=dict(color="white", width=1))
    )

    fig.update_layout(
        title_font_size=20,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)


df = load_data()


# Sidebar filters
st.sidebar.markdown('<div class="filter-title">Filters</div>', unsafe_allow_html=True)
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
    activities = get_options(df, "Activity")

    selected_donors = st.multiselect(
        "Donor number",
        donors,
        default=donors
    )

    selected_activities = st.multiselect(
        "Activity",
        activities,
        default=activities
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
    filtered_df = filtered_df[
        (filtered_df["Date"].dt.date >= start_date) &
        (filtered_df["Date"].dt.date <= end_date)
    ]


# Key figures
total_count = len(filtered_df)
female_count = count_gender(filtered_df, "female")
male_count = count_gender(filtered_df, "male")

local_count = count_displacement(filtered_df, ["non_displaced", "local", "host"])
idp_count = count_displacement(filtered_df, ["displaced"])
returnee_count = count_displacement(filtered_df, ["returnee", "return"])

pwd_count = count_disability(filtered_df)


st.subheader("Key figures")

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    render_card("👥", "Total participants", total_count)

with row1_col2:
    render_card("👩", "Women / girls", female_count)

with row1_col3:
    render_card("👨", "Men / boys", male_count)


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


tab_map, tab_overview, tab_location, tab_profile, tab_data = st.tabs([
    "Map",
    "Overview",
    "Location",
    "Profile",
    "Detailed data"
])


with tab_map:
    st.subheader("Map")

    st.markdown(
        """
        <div class="map-placeholder">
            <div class="map-placeholder-icon">🗺️</div>
            <div class="map-placeholder-title">Map will be added here</div>
            <div class="map-placeholder-text">
                This tab is reserved for the interactive Ukraine rayon map.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info("Next step: connect a valid GeoJSON file and make the map interactive.")


with tab_overview:
    make_bar(filtered_df, "Donor number", "Participants by donor")
    make_horizontal_bar(filtered_df, "Activity", "Top activities by participants", top_n=20)


with tab_location:
    make_bar(filtered_df, "Oblast", "Participants by oblast")
    make_horizontal_bar(filtered_df, "Rayon", "Participants by rayon", top_n=25)


with tab_profile:
    make_pie(filtered_df, "Gender", "Gender breakdown")
    make_pie(filtered_df, "Displacement", "Displacement status")
    make_pie(filtered_df, "Disability", "Disability status")
    make_bar(filtered_df, "ActDis", "Participants by age/disability category")


with tab_data:
    st.subheader("Detailed data")
    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="filtered_activity_data.csv",
        mime="text/csv"
    )
