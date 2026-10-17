"""
viz.py - Chart functions, so that every chart has the same simple style:
basic colors, labelled axes with units, and a hover tooltip.
"""

import pandas as pd
import plotly.express as px

# One basic color per meaning, used everywhere in the app
COLOR_MAIN = "blue"
COLOR_BAD = "red"
COLOR_GOOD = "green"
COLOR_UNKNOWN = "orange"


def funnel_chart(funnel):
    """Horizontal funnel: number of defibrillators left at each step."""
    fig = px.funnel(
        funnel,
        x="defibrillators",
        y="step",
        color_discrete_sequence=[COLOR_MAIN],
    )

    # Text inside the bars and in the tooltip
    fig.update_traces(
        texttemplate="%{x:,} (%{customdata[0]}%)",
        customdata=funnel[["percent"]],
        hovertemplate="<b>%{y}</b><br>%{x:,} defibrillators<br>%{customdata[0]}% of all declared<extra></extra>",
    )

    fig.update_layout(
        xaxis_title="Number of defibrillators",
        yaxis_title="Funnel step",
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
    )
    return fig


# Center and zoom used to show metropolitan France
FRANCE_CENTER = {"lat": 46.6, "lon": 2.4}
FRANCE_ZOOM = 4.3


def department_bubble_map(stats, metric, metric_label):
    """One bubble per department: size = population, color = chosen indicator."""
    data = stats.dropna(subset=["lat", "lon", metric])

    # Dark red = bad. For "per 10,000" indicators a LOW value is bad, so we reverse the scale.
    higher_is_better = metric in ("confirmed_per_10k", "declared_per_10k")
    color_scale = "Reds_r" if higher_is_better else "Reds"

    fig = px.scatter_map(
        data,
        lat="lat",
        lon="lon",
        size="population",
        color=metric,
        color_continuous_scale=color_scale,
        size_max=20,
        opacity=0.75,
        hover_name="label",
        hover_data={"population": ":,", metric: True, "lat": False, "lon": False},
        labels={metric: metric_label, "population": "Population (2023)"},
        center=FRANCE_CENTER,
        zoom=FRANCE_ZOOM,
        map_style="carto-positron",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=520,
                      coloraxis_colorbar=dict(title=""))
    return fig


def points_map(points, status_colors):
    """One dot per defibrillator, colored by its status."""
    # Center the map on the selected devices.
    # The zoom uses the 5%-95% range of positions, so that a few badly placed
    # devices (far from their department) do not force the map to zoom out.
    center = {"lat": points["lat"].median(), "lon": points["lon"].median()}
    lat_range = points["lat"].quantile(0.95) - points["lat"].quantile(0.05)
    lon_range = points["lon"].quantile(0.95) - points["lon"].quantile(0.05)
    spread = max(lat_range, lon_range)
    zoom = 10 if spread < 0.3 else 8.5 if spread < 1 else 7 if spread < 3 else 5

    fig = px.scatter_map(
        points,
        lat="lat",
        lon="lon",
        color="map_status",
        color_discrete_map=status_colors,
        category_orders={"map_status": list(status_colors.keys())},
        hover_name="city",
        hover_data={"access": True, "opening_hours": True, "equipment_status": True,
                    "lat": False, "lon": False, "map_status": False},
        labels={"map_status": "Status", "access": "Access",
                "opening_hours": "Declared hours", "equipment_status": "Equipment"},
        center=center,
        zoom=zoom,
        map_style="carto-positron",
    )
    fig.update_traces(marker=dict(size=6, opacity=0.7))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=520,
                      legend=dict(orientation="h", y=-0.05))
    return fig


def ranking_bar(stats, metric, metric_label, n, france_value):
    """Top n and bottom n departments for the chosen indicator, with the France value as a reference line."""
    ranked = stats.dropna(subset=[metric]).sort_values(metric, ascending=False)
    top = ranked.head(n).assign(group="Top")
    bottom = ranked.tail(n).assign(group="Bottom")
    data = pd.concat([top, bottom]).drop_duplicates("department")

    fig = px.bar(
        data.sort_values(metric),
        x=metric,
        y="label",
        color="group",
        color_discrete_map={"Top": COLOR_GOOD, "Bottom": COLOR_BAD},
        orientation="h",
        labels={metric: metric_label, "label": "Department", "group": ""},
        hover_data={"population": ":,", "declared": ":,", "group": False},
    )
    # Reference line: value for the whole selection
    fig.add_vline(x=france_value, line_dash="dash", line_color="black",
                  annotation_text=f"Whole selection: {france_value}",
                  annotation_position="top")
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=max(300, 28 * len(data)))
    return fig


def missing_bar(missing):
    """Horizontal bars: % of empty values for each important field."""
    fig = px.bar(
        missing.sort_values("percent"),
        x="percent",
        y="field",
        orientation="h",
        text="percent",
        color_discrete_sequence=[COLOR_UNKNOWN],
        labels={"percent": "Empty values (%)", "field": "Field"},
        hover_data={"empty": ":,"},
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    # Reference line: above 50%, the field is missing for most devices
    fig.add_vline(x=50, line_dash="dash", line_color=COLOR_BAD,
                  annotation_text="Half of the devices", annotation_position="top")
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=360,
                      xaxis=dict(range=[0, 105]))
    return fig


def hourly_line(hourly, chosen_day, chosen_hour, baseline_percent):
    """Share of ready-to-use devices open at each hour, one line per day."""
    fig = px.line(
        hourly,
        x="hour",
        y="percent",
        color="day",
        color_discrete_sequence=[COLOR_MAIN, COLOR_UNKNOWN, "purple"],
        markers=True,
        labels={"hour": "Hour of the day (h)", "percent": "Open devices (% of ready-to-use)",
                "day": "Day"},
        hover_data={"open_devices": ":,"},
    )
    # Reference line: devices confirmed 24/7 are always open
    fig.add_hline(y=baseline_percent, line_dash="dash", line_color=COLOR_GOOD,
                  annotation_text=f"Confirmed 24/7: {baseline_percent}%",
                  annotation_position="bottom right")
    # Marker for the moment chosen in the sidebar
    fig.add_vline(x=chosen_hour, line_dash="dot", line_color=COLOR_BAD,
                  annotation_text=f"Your emergency: {chosen_day} {chosen_hour}h",
                  annotation_position="top left")
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=400,
                      xaxis=dict(dtick=2), yaxis=dict(rangemode="tozero"))
    return fig
