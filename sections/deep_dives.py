"""
deep_dives.py - Where are the gaps?
1. A map (all of France by department, or every device when departments are selected)
2. A ranking of departments for the indicator chosen in the sidebar
3. Availability hour by hour
"""

import streamlit as st

from utils.prep import (department_stats, map_points, hourly_availability,
                        METRICS, MAP_STATUS_COLORS, DAY_NAMES)
from utils.viz import department_bubble_map, points_map, ranking_bar, hourly_line

# Maximum number of dots drawn on the detailed map (to keep the app fast)
MAX_POINTS = 40000
# Fixed seed so that the sample is always the same (reproducibility)
SEED = 42


def selection_value(stats, metric):
    """Value of an indicator for the whole selection (not an average of departments)."""
    if metric == "confirmed_per_10k":
        return round(stats["confirmed_24_7"].sum() / stats["population"].sum() * 10000, 2)
    if metric == "declared_per_10k":
        return round(stats["declared"].sum() / stats["population"].sum() * 10000, 2)
    if metric == "pct_hours_missing":
        return round(stats["hours_missing"].sum() / max(stats["working"].sum(), 1) * 100, 1)
    return round(stats["expired"].sum() / max(stats["working"].sum(), 1) * 100, 1)


def render(df, population, day, hour, metric_label, departments_selected):
    st.header("Where are the gaps?")

    metric = METRICS[metric_label]
    stats = department_stats(df, population)

    # ------------------------------------------------------------ 1. map
    st.subheader("Map")

    if stats.empty:
        st.info("No official department in the current selection.")
    elif not departments_selected:
        # Whole of France: one bubble per department
        best = stats.sort_values("confirmed_per_10k", ascending=False).iloc[0]
        worst = stats.sort_values("confirmed_per_10k").iloc[0]
        st.markdown(
            f"**Coverage is very uneven:** {best['label']} has **{best['confirmed_per_10k']}** "
            f"confirmed 24/7 defibrillators per 10,000 inhabitants, "
            f"{worst['label']} only **{worst['confirmed_per_10k']}**."
        )
        st.plotly_chart(department_bubble_map(stats, metric, metric_label), width="stretch")
        st.caption(
            f"Bubble map (alt text): one bubble per department, sized by population and colored by "
            f"'{metric_label}' (dark red = worst). Zoom out to see the overseas departments. "
            f"Select departments in the sidebar to see every defibrillator."
        )
    else:
        # Selected departments: one dot per working defibrillator
        points = map_points(df[df["valid_location"]])
        if len(points) > MAX_POINTS:
            st.caption(f"Showing a random sample of {MAX_POINTS:,} devices out of {len(points):,} "
                       f"to keep the map fast.")
            points = points.sample(MAX_POINTS, random_state=SEED)

        share_missing = (points["map_status"] == "Opening hours not provided").mean() * 100
        st.markdown(
            f"**{share_missing:.0f}% of the working defibrillators shown here have no opening hours "
            f"filled in** (orange dots): on the ground, nobody can know if they are reachable at night."
        )
        st.plotly_chart(points_map(points, MAP_STATUS_COLORS), width="stretch")
        st.caption(
            "Point map (alt text): one dot per working defibrillator. Green = confirmed 24/7, "
            "blue = limited hours, orange = hours not provided, red = expired battery or electrodes. "
            "Device names are not shown to protect privacy."
        )

    # ------------------------------------------------------------ 2. ranking
    st.subheader("Compare departments")
    if len(stats) < 2:
        st.info("Select at least two departments (or none) to compare them.")
    else:
        n = st.slider("Number of departments at the top and at the bottom",
                      min_value=3, max_value=15, value=5)
        whole = selection_value(stats, metric)
        st.markdown(f"Indicator: **{metric_label}** (change it in the sidebar). "
                    f"Dashed line = value for the whole selection.")
        st.plotly_chart(ranking_bar(stats, metric, metric_label, n, whole), width="stretch")
        st.caption(
            f"Bar chart (alt text): the {n} best (green) and {n} worst (red) departments for "
            f"'{metric_label}', compared with the whole selection ({whole})."
        )

    # ------------------------------------------------------------ 3. hour by hour
    st.subheader("What if the emergency happens at night?")

    # Always compare a weekday (Monday), Sunday, and the day chosen in the sidebar
    days = sorted({0, 6, day})
    hourly = hourly_availability(df, days)

    ready = int(df["step4_equipment"].sum())
    baseline = round(df["step5_24_7"].sum() / max(ready, 1) * 100, 1)
    chosen = hourly[(hourly["day"] == DAY_NAMES[day]) & (hourly["hour"] == hour)].iloc[0]
    peak = hourly["percent"].max()

    st.markdown(
        f"**On {DAY_NAMES[day]} at {hour}h, only {chosen['percent']}% of the ready-to-use "
        f"defibrillators are declared open**, compared with {peak}% at the busiest time."
    )
    st.plotly_chart(hourly_line(hourly, DAY_NAMES[day], hour, baseline), width="stretch")
    st.caption(
        "Line chart (alt text): share of ready-to-use defibrillators whose declared opening hours "
        "include each hour of the day. Devices with no opening hours are counted as not confirmed open. "
        "The green dashed line is the share confirmed 24/7."
    )
