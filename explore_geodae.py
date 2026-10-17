# explore_geodae.py
# Step 1: first look at the Geo'DAE defibrillator dataset
# Run with: python explore_geodae.py

import pandas as pd

# Path to the CSV file downloaded from data.gouv.fr
FILE_PATH = "data/raw/geodae.csv"

# 1. Find the separator used in the file (comma or semicolon)
#    We read only the first line and count both characters
with open(FILE_PATH, encoding="utf-8") as f:
    first_line = f.readline()

if first_line.count(";") > first_line.count(","):
    separator = ";"
else:
    separator = ","

print("Separator found:", separator)

# 2. Load the whole file into a table (DataFrame)
#    low_memory=False avoids warnings about mixed column types
df = pd.read_csv(FILE_PATH, sep=separator, encoding="utf-8", low_memory=False)

# 3. Size of the dataset
print("\nNumber of rows:", df.shape[0])
print("Number of columns:", df.shape[1])

# 4. List of all columns with their data type
print("\n--- Columns and types ---")
print(df.dtypes.to_string())

# 5. Percentage of missing values in each column (highest first)
print("\n--- Missing values (%) ---")
missing_percent = df.isna().mean() * 100
missing_percent = missing_percent.round(1).sort_values(ascending=False)
print(missing_percent.to_string())

# 6. Number of fully duplicated rows
print("\nDuplicated rows:", df.duplicated().sum())

# 7. Show 3 example rows
#    .T flips the table so each column is shown on its own line (easier to read)
print("\n--- 3 example rows ---")
print(df.head(3).T.to_string())
