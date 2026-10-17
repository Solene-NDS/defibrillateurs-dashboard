"""
overview.py - KPIs (linked to the filters) and the funnel of the story.
"""

import streamlit as st

from utils.prep import make_funnel, open_at, DAY_NAMES
from utils.viz import funnel_chart


def render(df, day, hour):
    st.header("From declared to really usable")

    # ------------------------------------------------------------ numbers for the KPIs
    total = len(df)
    confirmed_24_7 = int(df["step5_24_7"].sum())

    working = df[df["step3_working"]]
    expired = int((working["equipment_status"] == "Expired").sum())

    # Defibrillators ready to use (step 4) that are open at the chosen time
    ready = df[df["step4_equipment"]]
    open_now = int(open_at(ready, day, hour).sum())

    def pct(part, whole):
        return round(part / whole * 100, 1) if whole > 0 else 0

    # ------------------------------------------------------------ headline insight
    st.markdown(
        f"**Only {pct(confirmed_24_7, total)}% of the declared defibrillators are "
        f"confirmed usable 24/7** in the current selection."
    )

    # ------------------------------------------------------------ KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Declared defibrillators", f"{total:,}",
              help="All devices in the Géo'DAE database for the current filters.")
    c2.metric("Confirmed 24/7", f"{confirmed_24_7:,}",
              f"{pct(confirmed_24_7, total)}% of declared", delta_color="off",
              help="Usable record, valid location, declared working, equipment not "
                   "expired and opening hours = 24/7.")
    c3.metric("Expired battery or electrodes", f"{expired:,}",
              f"{pct(expired, len(working))}% of working devices", delta_color="off",
              help="Devices declared 'working' whose battery or electrodes expiry date has passed.")
    c4.metric(f"Open on {DAY_NAMES[day]} at {hour}h", f"{open_now:,}",
              f"{pct(open_now, total)}% of declared", delta_color="off",
              help="Ready-to-use devices whose declared opening hours include this time. "
                   "Change the day and hour in the sidebar.")

    # ------------------------------------------------------------ funnel
    st.subheader("The funnel: where do we lose defibrillators?")
    funnel = make_funnel(df)
    st.plotly_chart(funnel_chart(funnel), width="stretch")
    st.caption(
        "Funnel chart (alt text): each bar shows how many defibrillators are left after one more check. "
        "The biggest drop is the last step, because most devices have no opening hours filled in."
    )
