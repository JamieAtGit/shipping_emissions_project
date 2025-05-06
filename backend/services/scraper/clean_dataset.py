# clean_dataset.py

# clean_dataset.py
import pandas as pd

df = pd.read_csv("ml_model/eco_dataset.csv")

# Normalize casing & strip whitespace
df["true_eco_score"] = df["true_eco_score"].astype(str).str.strip().str.upper()

# Only allow valid scores
valid_scores = ["A+", "A", "B", "C", "D", "E", "F"]
before = len(df)
df = df[df["true_eco_score"].isin(valid_scores)]
after = len(df)

# Save cleaned CSV
df.to_csv("ml_model/eco_dataset.csv", index=False)
print(f"✅ Cleaned dataset: {before - after} invalid rows removed.")
