"""
data_quality.py - Missing values, duplicates, validation checks and limitations.
In this story, data quality is not a side topic: it IS part of the problem.
"""

import streamlit as st

from utils.prep import missing_values, quality_checks
from utils.viz import missing_bar


def render(df, population):
    st.header("Data quality & limitations")

    missing = missing_values(df)
    checks = quality_checks(df, population)

    # ------------------------------------------------------------ headline
    hours_missing = missing.loc[missing["field"] == "Opening hours", "percent"].iloc[0]
    battery_missing = missing.loc[missing["field"] == "Battery expiry date", "percent"].iloc[0]
    st.markdown(
        f"**The official database cannot answer the most important questions:** opening hours are "
        f"missing for {hours_missing}% of the devices and the battery expiry date for {battery_missing}%."
    )

    # ------------------------------------------------------------ missing values
    st.subheader("Missing values")
    st.plotly_chart(missing_bar(missing), width="stretch")
    st.caption(
        "Bar chart (alt text): percentage of empty values for each important field, "
        "for the current selection. The red dashed line marks 50%."
    )

    # ------------------------------------------------------------ validation checks
    st.subheader("Validation checks")
    st.markdown("Every row was tested. Problematic rows are **flagged, not deleted**, "
                "so that the funnel can show where devices are lost.")
    st.dataframe(checks, hide_index=True, width="stretch")

    # ------------------------------------------------------------ limitations
    st.subheader("Assumptions and limitations")
    with st.expander("Read the assumptions behind the numbers", expanded=False):
        st.markdown(
            """
- **Declarative data.** Operators fill in the database themselves. A department that looks
  well equipped may simply be one where operators filled in their records more carefully.
  The numbers show what is **confirmed in the database**, not what exists on the ground.
- **"Mo-Su off" = not provided.** About 72% of devices have this value although they are
  declared working. We assume it is the default value of the form, not a real "closed every day".
- **Expiry dates** are compared with a fixed reference date (17 October 2026) so that results
  are reproducible.
- **Location check:** a simple box around metropolitan France is used; overseas devices are
  accepted when their department is overseas. Corsican postal codes are split into 2A / 2B
  with an approximation.
- **Population:** Insee municipal population 2023. Mayotte and overseas collectivities
  (Saint-Pierre-et-Miquelon, Saint-Barthélemy, Polynesia...) have no value.
- **No data on where cardiac arrests happen.** Population is only a proxy for the need.
- **No causality is claimed.** The dashboard describes gaps; it does not explain their causes.
"""
        )

    with st.expander("Ethics and privacy", expanded=False):
        st.markdown(
            """
- Some records contain the **name of a person** (e.g. the contact or the device name).
  Names are **never displayed**; the app only shows cities, access type, hours and aggregates.
- Data: Licence Ouverte 2.0 (Etalab) — free reuse with attribution, cited at the top of the page.
"""
        )
