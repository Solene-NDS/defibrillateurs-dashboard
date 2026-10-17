"""
conclusions.py - Key insights, implications and next steps.
The numbers are recomputed for the current selection.
"""

import streamlit as st

from utils.prep import open_at, department_stats


def render(df, population):
    st.header("Key insights & next steps")

    # ------------------------------------------------------------ numbers for the selection
    total = len(df)
    confirmed = int(df["step5_24_7"].sum())
    working = df[df["step3_working"]]
    ready = df[df["step4_equipment"]]

    def pct(part, whole):
        return round(part / whole * 100, 1) if whole > 0 else 0

    hours_missing = pct(int((working["hours_category"] == "Not provided").sum()), len(working))
    expired = pct(int((working["equipment_status"] == "Expired").sum()), len(working))

    # Open on Monday at 10h (office time) vs Sunday at 3h (night)
    open_day = pct(int(open_at(ready, 0, 10).sum()), len(ready))
    open_night = pct(int(open_at(ready, 6, 3).sum()), len(ready))

    # ------------------------------------------------------------ insights
    st.subheader("What the data shows")
    st.markdown(
        f"""
1. **A big gap between declared and usable.** Out of {total:,} declared defibrillators,
   only **{confirmed:,} ({pct(confirmed, total)}%)** are confirmed usable at any time.
2. **The main problem is missing information, not missing devices.** {hours_missing}% of the
   working devices have no opening hours, so nobody can know if they are reachable at night.
3. **Night and weekends are the weak spot.** {open_day}% of ready-to-use devices are declared
   open on Monday at 10h, but only {open_night}% on Sunday at 3h.
4. **Equipment is not always ready.** {expired}% of the devices declared working have an expired
   battery or electrodes.
"""
    )

    stats = department_stats(df, population)
    if len(stats) >= 2:
        best = stats.sort_values("confirmed_per_10k", ascending=False).iloc[0]
        worst = stats.sort_values("confirmed_per_10k").iloc[0]
        st.markdown(
            f"5. **Strong inequalities between territories.** From {best['confirmed_per_10k']} "
            f"confirmed 24/7 devices per 10,000 inhabitants ({best['label']}) "
            f"to {worst['confirmed_per_10k']} ({worst['label']})."
        )

    # ------------------------------------------------------------ implications
    st.subheader("What should be done")
    st.success(
        """
- **Operators:** fill in the opening hours and expiry dates — it costs nothing and turns an
  "unknown" device into a usable one.
- **Health agencies (ARS) and city halls:** make the opening-hours field mandatory, run update
  campaigns, and favour **outdoor devices accessible 24/7** for new installations.
- **Priority areas:** departments at the bottom of the ranking, starting with overseas territories.
"""
    )

    # ------------------------------------------------------------ next steps
    st.subheader("Next steps for the analysis")
    st.markdown(
        """
- Check with the database managers whether "Mo-Su off" is really a default value.
- Compare with data on **where cardiac arrests actually happen**, instead of using population as a proxy.
- Follow the database over time to see if the share of usable devices improves.
"""
    )
