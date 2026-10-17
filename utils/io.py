"""
io.py - Load the clean data files.

The files are produced by the notebooks clean_geodae.ipynb and
population_departments.ipynb. They are small, so they are stored in the repo.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# Project folder = the folder that contains app.py (one level above utils/)
PROJECT_DIR = Path(__file__).resolve().parent.parent

DAE_PATH = PROJECT_DIR / "data" / "clean" / "geodae_clean.parquet"
POP_PATH = PROJECT_DIR / "data" / "clean" / "population_departments.csv"

# Text shown under the title (sources and licence)
SOURCE_TEXT = (
    "Sources: Géo'DAE – Base nationale des défibrillateurs (Atlasanté) and "
    "Populations municipales 1968–2023 (Insee), both on data.gouv.fr – "
    "Licence Ouverte 2.0"
)


@st.cache_data(show_spinner="Loading defibrillator data...")
def load_dae():
    """Load the clean defibrillator table (one row per defibrillator)."""
    return pd.read_parquet(DAE_PATH)


@st.cache_data
def load_population():
    """Load the population of each department (2023)."""
    # dtype=str keeps codes like "01" with their first zero
    return pd.read_csv(POP_PATH, dtype={"department": str})
