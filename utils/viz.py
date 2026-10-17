"""
viz.py - Chart functions, so that every chart has the same simple style:
basic colors, labelled axes with units, and a hover tooltip.
"""

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
