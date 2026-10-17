"""
intro.py - The hook and the context of the story.
"""

import streamlit as st


def render():
    st.header("Why this matters")

    st.markdown(
        """
When someone has a **cardiac arrest**, every minute counts.
According to the official description of the national database, barely
**1 person in 10 survives**, often because nobody acted in time.
A **defibrillator (AED)** used in the first minutes can change that.

Since a law of **June 2018**, every operator of an AED in France must declare it in
a national database called **Géo'DAE**. Today it contains about **190,000** devices.

**But a defibrillator only helps if it can actually be used:** it must exist,
be at the right place, work, have a valid battery and electrodes,
and be **accessible at the moment of the emergency** — at night or on a Sunday too.
"""
    )

    st.info(
        "**Question of this dashboard:** out of all the defibrillators declared in France, "
        "how many are *confirmed* usable at any time — and where are the gaps?"
    )

    with st.expander("Who is this dashboard for?"):
        st.markdown(
            """
- **Local decision makers** (city halls, regional health agencies):
  where to install new AEDs and which records to update.
- **Citizens**: understand that a defibrillator on a map is not always available.
"""
        )
