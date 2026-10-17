"""
prep.py - Small data preparation functions used by the app:
filters, funnel table and opening-hours reader.
"""

import numpy as np
import pandas as pd
import streamlit as st

from utils.departments import DEPARTMENT_NAMES, department_label

# Day codes used in the opening-hours text (Monday = 0 ... Sunday = 6)
DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Names of the funnel steps, in order, with the column that holds each step
FUNNEL_STEPS = [
    ("0. All declared", None),
    ("1. Usable record", "step1_record"),
    ("2. Valid location", "step2_location"),
    ("3. Declared working", "step3_working"),
    ("4. Equipment not expired", "step4_equipment"),
    ("5. Confirmed 24/7", "step5_24_7"),
]

# Indicators the user can choose in the sidebar to compare departments
# (label shown to the user -> column name in the department table)
METRICS = {
    "Confirmed 24/7 per 10,000 inhabitants": "confirmed_per_10k",
    "Declared per 10,000 inhabitants": "declared_per_10k",
    "% of working devices with no opening hours": "pct_hours_missing",
    "% of working devices with expired equipment": "pct_expired",
}

# Same reference date as in the cleaning notebook (used for expiry checks)
REFERENCE_DATE = pd.Timestamp("2026-10-17")

# A device more than this distance from the center of its department is suspicious
FAR_FROM_DEPARTMENT_KM = 100

# Status of each device on the detailed map, with one basic color each
MAP_STATUS_COLORS = {
    "Confirmed 24/7": "green",
    "Limited hours": "blue",
    "Opening hours not provided": "orange",
    "Expired battery or electrodes": "red",
}


# ---------------------------------------------------------------- filters
def filter_data(df, departments, access_types):
    """Keep only the rows that match the sidebar filters.
    An empty list means 'no filter'."""
    mask = pd.Series(True, index=df.index)
    if departments:
        mask = mask & df["department"].isin(departments)
    if access_types:
        mask = mask & df["access_type"].isin(access_types)
    return df[mask]


# ---------------------------------------------------------------- funnel
def make_funnel(df):
    """Return a table with the number of defibrillators at each funnel step."""
    rows = []
    for step_name, column in FUNNEL_STEPS:
        count = len(df) if column is None else int(df[column].sum())
        rows.append({"step": step_name, "defibrillators": count})

    funnel = pd.DataFrame(rows)
    total = max(len(df), 1)  # avoid dividing by zero
    funnel["percent"] = (funnel["defibrillators"] / total * 100).round(1)
    return funnel


# ---------------------------------------------------------------- departments
def department_stats(df, population):
    """
    One row per department with counts, rates and a map position.
    Only departments that have a population (official departments) are kept.
    """
    working = df["step3_working"]

    # Helper columns: one True/False per thing we want to count
    data = df.assign(
        working=working,
        expired=working & (df["equipment_status"] == "Expired"),
        hours_missing=working & df["hours_category"].isin(["Not provided", "Unreadable"]),
    )

    # Count per department
    stats = data.groupby("department").agg(
        declared=("id", "size"),
        working=("working", "sum"),
        confirmed_24_7=("step5_24_7", "sum"),
        expired=("expired", "sum"),
        hours_missing=("hours_missing", "sum"),
    ).reset_index()

    # Map position of each department = median position of its defibrillators
    positions = (df[df["valid_location"]]
                 .groupby("department")[["lat", "lon"]]
                 .median()
                 .reset_index())

    # Join: population (inner = keep only real departments), then positions
    stats = population.merge(stats, on="department", how="inner")
    stats = stats.merge(positions, on="department", how="left")

    # Rates
    stats["confirmed_per_10k"] = (stats["confirmed_24_7"] / stats["population"] * 10000).round(2)
    stats["declared_per_10k"] = (stats["declared"] / stats["population"] * 10000).round(2)
    working_count = stats["working"].where(stats["working"] > 0)  # avoid dividing by zero
    stats["pct_hours_missing"] = (stats["hours_missing"] / working_count * 100).round(1)
    stats["pct_expired"] = (stats["expired"] / working_count * 100).round(1)

    # Readable label, e.g. "55 - Meuse"
    stats["label"] = stats["department"].map(department_label)
    return stats


def known_departments(df):
    """Sorted list of the official department codes present in the data."""
    codes = df["department"].dropna().unique()
    return sorted(code for code in codes if code in DEPARTMENT_NAMES)


# ---------------------------------------------------------------- data quality
def missing_values(df):
    """Percentage of empty values for the fields that matter for the story."""
    fields = {
        "Battery expiry date": df["battery_expiry"].isna(),
        "Electrodes expiry date": df["electrodes_expiry"].isna(),
        "Installation date": df["install_date"].isna(),
        "Status (active / inactive)": df["status"].isna(),
        "City INSEE code": df["insee_code"].isna(),
        # The default value "Mo-Su off" is counted as empty (see the cleaning notebook)
        "Opening hours": df["hours_category"] == "Not provided",
        "Last maintenance date": df["last_maintenance"].isna(),
    }
    rows = [{"field": name, "empty": int(is_empty.sum()),
             "percent": round(is_empty.mean() * 100, 1)}
            for name, is_empty in fields.items()]
    return pd.DataFrame(rows)


def distance_km(lat1, lon1, lat2, lon2):
    """Distance in km between two points on Earth (haversine formula)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def far_from_department(df):
    """True/False column: is the device more than 100 km from the center of its department?"""
    located = df[df["valid_location"] & df["department"].notna()]
    # Center of each department = median position of its devices
    centers = located.groupby("department")[["lat", "lon"]].median()
    center_lat = df["department"].map(centers["lat"])
    center_lon = df["department"].map(centers["lon"])

    distance = distance_km(df["lat"], df["lon"], center_lat, center_lon)
    return df["valid_location"] & (distance > FAR_FROM_DEPARTMENT_KM)


def quality_checks(df, population):
    """Table of validation checks: what we tested, how many rows fail, and what we did."""
    n = max(len(df), 1)
    no_population = ~df["department"].isin(population["department"])

    checks = [
        ("Flagged as duplicate in the database", df["is_duplicate"],
         "Removed at funnel step 1"),
        ("Not validated yet (pending or doubtful)", df["validation_status"] != "validées",
         "Removed at funnel step 1"),
        ("Marked 'to delete'", df["status"] == "A supprimer",
         "Removed at funnel step 1"),
        ("Mobile device (no fixed place)", df["is_mobile"],
         "Removed at funnel step 1"),
        ("Coordinates missing, equal to 0 or outside France", ~df["valid_location"],
         "Removed at funnel step 2"),
        (f"Located more than {FAR_FROM_DEPARTMENT_KM} km from its department", far_from_department(df),
         "Kept, but its department may be wrong"),
        ("Department not found or not an official department", no_population,
         "Kept on the map, no 'per 10,000 inhabitants' value"),
        ("Opening hours = default value ('Mo-Su off')", df["hours_category"] == "Not provided",
         "Treated as 'not provided', not as 'closed'"),
        ("Opening hours text unreadable", df["hours_category"] == "Unreadable",
         "Not confirmed open"),
        ("Battery or electrodes expired", df["equipment_status"] == "Expired",
         "Removed at funnel step 4"),
        ("Last maintenance date in the future", df["last_maintenance"] > REFERENCE_DATE,
         "Kept, date considered as a typo"),
    ]

    rows = [{"Check": name, "Rows": int(failed.sum()),
             "% of rows": round(failed.sum() / n * 100, 1), "Action": action}
            for name, failed, action in checks]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- detailed map
def map_points(df):
    """Working devices with a valid location, with a status used for the map colors."""
    points = df[df["step3_working"]].copy()

    # One status per device (the first rule that matches wins)
    points["map_status"] = "Limited hours"
    points.loc[points["hours_category"].isin(["Not provided", "Unreadable"]),
               "map_status"] = "Opening hours not provided"
    points.loc[points["hours_category"] == "24/7", "map_status"] = "Confirmed 24/7"
    points.loc[points["equipment_status"] == "Expired",
               "map_status"] = "Expired battery or electrodes"

    # Readable access type for the tooltip
    points["access"] = points["access_type"].map({"Intérieur": "Indoor", "Extérieur": "Outdoor"})
    return points


# ---------------------------------------------------------------- opening hours
def parse_opening_hours(text):
    """
    Read an opening-hours text (OpenStreetMap style) and return:
    - "always" for 24/7,
    - a dictionary {day number: list of (start minute, end minute)},
    - None if the text cannot be read.
    Same function as in the cleaning notebook.
    """
    if not isinstance(text, str):
        return None
    text = text.strip()
    if text == "24/7":
        return "always"

    # Start with every day closed
    schedule = {day: [] for day in range(7)}

    # Rules are separated by ";"  (e.g. "Mo-Fr 09:00-18:00; Sa-Su off")
    for rule in text.split(";"):
        rule = rule.strip()
        if rule == "" or rule.startswith("PH"):
            continue  # skip empty parts and public holidays

        parts = rule.split(" ", 1)
        if len(parts) != 2:
            return None
        days_text, times_text = parts

        # Find the days of the rule (e.g. "Mo-Fr" or "Sa,Su")
        days = []
        for chunk in days_text.split(","):
            if "-" in chunk:
                first, last = chunk.split("-", 1)
                if first not in DAYS or last not in DAYS:
                    return None
                day = DAYS.index(first)
                while True:
                    days.append(day)
                    if day == DAYS.index(last):
                        break
                    day = (day + 1) % 7
            elif chunk in DAYS:
                days.append(DAYS.index(chunk))
            else:
                return None

        # "off" means closed on these days
        if times_text.strip().lower() == "off":
            for day in days:
                schedule[day] = []
            continue

        # Read the time slots (e.g. "09:00-12:00,14:00-18:00")
        slots = []
        for slot in times_text.split(","):
            try:
                start, end = slot.strip().split("-")
                start_h, start_m = start.split(":")
                end_h, end_m = end.split(":")
                slots.append((int(start_h) * 60 + int(start_m),
                              int(end_h) * 60 + int(end_m)))
            except ValueError:
                return None
        for day in days:
            schedule[day] = slots

    return schedule


def is_open(schedule, day, minute):
    """True if a parsed schedule is open on this day (0-6) at this minute of the day."""
    if schedule == "always":
        return True
    if not isinstance(schedule, dict):
        return False  # unreadable text: we cannot confirm it is open

    for start, end in schedule[day]:
        if start <= end and start <= minute <= end:
            return True
        # Slot that goes past midnight (e.g. 22:00-06:00)
        if end < start and (minute >= start or minute <= end):
            return True
    return False


@st.cache_data
def parse_all_hours(texts):
    """Parse each different opening-hours text once (the result is cached)."""
    return {text: parse_opening_hours(text) for text in texts}


def open_at(df, day, hour):
    """Return a True/False column: is each defibrillator open on this day at this hour?"""
    minute = hour * 60
    schedules = parse_all_hours(tuple(df["opening_hours"].dropna().unique()))
    open_map = {text: is_open(schedule, day, minute) for text, schedule in schedules.items()}
    return df["opening_hours"].map(open_map).fillna(False).astype(bool)


def hourly_availability(df, days):
    """
    For each chosen day and each hour (0-23): how many ready-to-use devices are open?
    Returns a table with columns: day, hour, open_devices, percent.
    """
    ready = df[df["step4_equipment"]]
    total = max(len(ready), 1)

    rows = []
    for day in days:
        for hour in range(24):
            count = int(open_at(ready, day, hour).sum())
            rows.append({"day": DAY_NAMES[day], "hour": hour,
                         "open_devices": count,
                         "percent": round(count / total * 100, 1)})
    return pd.DataFrame(rows)
