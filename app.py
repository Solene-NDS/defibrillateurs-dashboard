"""
app.py - Main file of the Streamlit dashboard.

Run it from the project folder with:
    streamlit run app.py
"""

import streamlit as st

from utils.io import load_dae, load_population, SOURCE_TEXT
from utils.prep import filter_data, DAY_NAMES
from sections import intro, overview, deep_dives, data_quality, conclusions

# ---------------------------------------------------------------- page settings
st.set_page_config(
    page_title="Defibrillators in France",
    page_icon="❤️",
    layout="wide",
)

# ---------------------------------------------------------------- data (cached)
dae = load_dae()
population = load_population()

# ---------------------------------------------------------------- title
st.title("A defibrillator nearby... but can you actually use it?")
st.caption(SOURCE_TEXT)

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Filters")

    departments = st.multiselect(
        "Department(s)",
        options=sorted(dae["department"].dropna().unique()),
        help="Leave empty to see the whole of France.",
    )

    access_labels = {"Intérieur": "Indoor", "Extérieur": "Outdoor"}
    access_types = st.multiselect(
        "Access type",
        options=list(access_labels.keys()),
        format_func=lambda value: access_labels[value],
        help="Outdoor devices can usually be reached at any time.",
    )

    st.header("When does the emergency happen?")
    day_name = st.selectbox("Day", DAY_NAMES, index=6)  # Sunday by default
    hour = st.slider("Hour", min_value=0, max_value=23, value=3, format="%dh")
    st.caption("Default: Sunday at 3 am, a moment when most buildings are closed.")

# Apply the filters
filtered = filter_data(dae, departments, access_types)
day = DAY_NAMES.index(day_name)

if filtered.empty:
    st.warning("No defibrillator matches these filters. Please change the selection.")
    st.stop()

# ---------------------------------------------------------------- story sections
intro.render()
st.divider()
overview.render(filtered, day, hour)
st.divider()
deep_dives.render(filtered, population, day, hour)
st.divider()
data_quality.render(filtered)
st.divider()
conclusions.render(filtered)
