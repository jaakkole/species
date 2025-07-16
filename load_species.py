import pandas as pd
from fuzzywuzzy import process

# Load species database CSV with correct separator and encoding
df = pd.read_csv('species_list.csv', sep=';', encoding='utf-8-sig')

# Print column names to help verify correct headers
print("CSV columns:", df.columns)

print(f"Loaded {len(df)} species from CSV.")

# Function to fuzzy match user input species against database Finnish names
def fuzzy_match_species(input_species, species_names, limit=3, threshold=80):
    """
    Matches input_species (string) against species_names (list) using fuzzy matching.
    Returns list of tuples: (matched_name, score) above threshold, limited by 'limit'.
    """
    matches = process.extract(input_species, species_names, limit=limit)
    filtered_matches = [(name, score) for name, score in matches if score >= threshold]
    return filtered_matches

def main():
    # Extract species Finnish names as list for matching
    # Adjust the column name here after checking the print output!
    species_names = df['FinnishName'].tolist()

    # Example: Ask user for species name input
    user_input = input("Enter species name to search: ").strip()

    results = fuzzy_match_species(user_input, species_names)

    if results:
        print("Matches found:")
        for name, score in results:
            # Get full row for the matched species
            row = df[df['FinnishName'] == name].iloc[0]
            print(f"- {name} (Score: {score})")
            print(f"  Scientific Name: {row['ScientificName']}")
