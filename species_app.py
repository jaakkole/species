 import pandas as pd
from rapidfuzz import process, fuzz
import streamlit as st
import requests

st.set_page_config(page_title="Endangered Species Checker", layout="centered")

# App title and instructions
st.title("🦐 Endangered Species Checker")
st.markdown("""
Paste your species data directly from **any register, eg. POHJE** aquatic species results below.
The app handles typos, scientific names, and Finnish names.

After pasting, press **Submit** to analyze the species list.
""")

# Text input area
species_text = st.text_area("Paste your species list here", height=300)

# Load species database CSV
@st.cache_data
def load_species_data():
    df = pd.read_csv('species_list.csv', sep=';', encoding='utf-8')
    all_names = pd.concat([df['FinnishName'], df['ScientificName']]).dropna().str.lower().str.strip().unique()
    return df, all_names

df, all_species_names = load_species_data()

# Fetch occurrence data from GBIF API with pagination and coordinate filtering
def get_gbif_occurrences(scientific_name, max_records=1000):
    coordinates = []
    limit = 300  # max records per request (GBIF API limit)
    offset = 0
    headers = {"User-Agent": "species_checker/1.0"}

    while offset < max_records:
        url = (
            f"https://api.gbif.org/v1/occurrence/search?"
            f"scientificName={scientific_name}&limit={limit}&offset={offset}&hasCoordinate=true"
        )
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()

        results = data.get('results', [])
        if not results:
            break  # no more data

        for record in results:
            lat = record.get('decimalLatitude')
            lon = record.get('decimalLongitude')
            if lat is not None and lon is not None:
                coordinates.append((lat, lon))

        offset += limit
        if len(results) < limit:
            break  # last page

    return coordinates

# Main analyze button logic
if st.button("🔍 Analyze"):
    if not species_text.strip():
        st.warning("Please paste species data first.")
    else:
        # Process input lines to species names (scientific or Finnish)
        input_lines = species_text.strip().split('\n')
        input_species = []
        for line in input_lines:
            line = line.strip()
            if not line or line.isupper():
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0].isalpha() and parts[1].isalpha():
                input_species.append(f"{parts[0]} {parts[1]}".lower())
            elif len(parts) >= 1 and parts[0].isalpha():
                input_species.append(parts[0].lower())

        # Fuzzy match input species to known species names
        threshold = 80
        found = []
        matched_species_set = set()
        for sp in input_species:
            match, score, _ = process.extractOne(sp, all_species_names, scorer=fuzz.token_sort_ratio)
            if score >= threshold:
                matched_rows = df[
                    (df['FinnishName'].str.lower().str.strip() == match) |
                    (df['ScientificName'].str.lower().str.strip() == match)
                ]
                for _, row in matched_rows.iterrows():
                    found.append((sp, match, score, row))
                    matched_species_set.add(row['ScientificName'])

        total_input_species = len(set(input_species))
        total_matched_species = len(matched_species_set)

        st.markdown(f"### Summary")
        st.markdown(f"- Total unique species in input data: **{total_input_species}**")
        st.markdown(f"- Total species matched in endangered species database: **{total_matched_species}**")

        if found:
            st.success(f"✅ Found {len(found)} endangered species matches:")

            matched_df = pd.DataFrame([row for _, _, _, row in found]).drop_duplicates(subset=['ScientificName'])
            st.dataframe(matched_df)

            # List matched species names
            for inp, matched, score, row in found:
                scientific_name = row['ScientificName']
                st.markdown(f"**Input:** `{inp}` → **Matched:** `{matched}` (score {score})")

        else:
            st.info("No endangered species found.")
