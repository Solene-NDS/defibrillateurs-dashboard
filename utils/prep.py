"""
prep.py - Small data preparation functions used by the app:
filters, funnel table and opening-hours reader.
"""

import pandas as pd
import streamlit as st

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
