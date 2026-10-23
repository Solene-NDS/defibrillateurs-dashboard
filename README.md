# A defibrillator nearby... but can you actually use it?

Data storytelling dashboard built with Streamlit, about the defibrillators (AEDs) declared in France.

**Author:** Solène N'DAH-SEKOU (20251449), EFREI Paris, Data Engineering, group DE2
**Live app:** https://defibrillateurs-france.streamlit.app
**Repository:** https://github.com/Solene-NDS/defibrillateurs-dashboard
**Demo video:** submitted with the project

## The problem

France has about 190,000 declared defibrillators, but we don't know how many can actually be used when a cardiac arrest happens, especially at night or on weekends. A defibrillator only helps if it is correctly registered, at the right place, working, with a valid battery and electrodes, and accessible at the moment of the emergency.

## Questions answered

1. How many declared defibrillators are confirmed usable 24/7?
2. At which step are devices "lost": database quality, location, working state, expired equipment or opening hours?
3. Which departments are best and worst covered, relative to their population?
4. How does availability change with the day and the hour?
5. How reliable is the national database itself?

**Audience:** local decision makers (city halls, regional health agencies) and citizens.

## Main findings

- Only **28,191 out of 189,536 defibrillators (14.9%)** are confirmed usable 24/7.
- The main reason is missing information: **72% of the devices have no opening hours** filled in.
- On Sunday at 3am, only **20.2%** of the ready-to-use devices are declared open, against **30.5%** on Monday at 10am.
- **14.2%** of the devices declared working have an expired battery or electrodes.
- Coverage is very uneven: from **21.91** confirmed 24/7 devices per 10,000 inhabitants in the Meuse to **0.03** in Guadeloupe.

## Data

Both datasets come from data.gouv.fr and are published under the Licence Ouverte 2.0 (Etalab).

| Dataset | Producer | Use |
|---|---|---|
| [Géo'DAE – Base nationale des défibrillateurs](https://www.data.gouv.fr/datasets/geodae-base-nationale-des-defibrillateurs) | Atlasanté | One row per defibrillator: location, working state, expiry dates, opening hours |
| [Populations municipales de 1968 à 2023](https://www.data.gouv.fr/datasets/populations-municipales-de-1968-a-2023) | Insee | Population of each department in 2023 |

The two tables are joined on the **department code**, which gives the number of defibrillators per 10,000 inhabitants.

The raw files are not stored in this repository because they are too large. The notebooks download them automatically if they are missing. The clean files used by the app are in `data/clean/`.

## Data preparation

1. `explore_geodae.ipynb`: first look at the raw file (size, columns, missing values, duplicates).
2. `clean_geodae.ipynb`: keeps 19 useful columns, converts dates, rebuilds the department from the INSEE code or the postal code, checks locations and expiry dates, reads the opening hours, adds one column per funnel step, and saves `data/clean/geodae_clean.parquet` (78.5 MB of CSV reduced to 9.9 MB).
3. `population_departments.ipynb`: extracts the 2023 population of each department, checks it (100 departments, 68.1 million inhabitants, no duplicates) and saves `data/clean/population_departments.csv`.

## How to run the app

```bash
pip install -r requirements.txt
streamlit run app.py
```

To rebuild the clean data from scratch, run the three notebooks in the order above.

## Project structure

```
app.py                     main file: title, sidebar filters, sections
requirements.txt
data/clean/                clean data used by the app
utils/
    io.py                  data loading (cached with st.cache_data)
    prep.py                filters, funnel, department statistics, opening-hours reader, quality checks
    viz.py                 chart functions
    departments.py         department names
sections/
    intro.py               hook and context
    overview.py            KPIs and funnel
    deep_dives.py          map, department ranking, hour-by-hour availability
    data_quality.py        missing values, validation checks, limitations
    conclusions.py         insights, implications, next steps
*.ipynb                    exploration and cleaning notebooks
```

## Assumptions and limitations

- The data is **declarative**: operators fill in their own records, so a well-ranked department may simply have better-filled records. The dashboard shows what is confirmed in the database, not what exists on the ground.
- The opening-hours value **"Mo-Su off"** appears for 72% of the devices although they are declared working. It is treated as a default form value ("not provided"), not as "closed".
- Expiry dates are compared with a fixed reference date (17 October 2026) so that results are reproducible.
- Population is only a proxy for the need, since there is no data on where cardiac arrests happen.
- Mayotte and the overseas collectivities have no population value.
- No causal claim is made: the dashboard describes gaps, not their causes.

## Ethics

Some records contain the name of a person. Names are never displayed in the app, which only shows cities, access type, opening hours and aggregated figures.
