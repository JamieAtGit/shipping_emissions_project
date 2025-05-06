import pandas as pd
import os

def load_material_co2_data():
    path = os.path.join("ml_model", "defra_material_intensity.csv")
    if not os.path.exists(path):
        print("⚠️ CO2 data file not found:", path)
        return {}

    df = pd.read_csv(path)
    co2_map = dict(zip(df["material"].str.lower(), df["co2_per_kg"]))
    return co2_map
