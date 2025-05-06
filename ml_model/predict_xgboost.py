import pandas as pd
import xgboost as xgb
import joblib
import os
import numpy as np
import time
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# === Load model and encoders
script_dir = os.path.dirname(__file__)
model_dir = os.path.join(script_dir, "ml_model")

booster = xgb.Booster()
booster.load_model(os.path.join(model_dir, "xgb_model.json"))

encoders_dir = os.path.join(model_dir, "xgb_encoders")
material_enc = joblib.load(os.path.join(encoders_dir, "material_encoder.pkl"))
transport_enc = joblib.load(os.path.join(encoders_dir, "transport_encoder.pkl"))
recyclability_enc = joblib.load(os.path.join(encoders_dir, "recyclability_encoder.pkl"))
origin_enc = joblib.load(os.path.join(encoders_dir, "origin_encoder.pkl"))
label_enc = joblib.load(os.path.join(encoders_dir, "label_encoder.pkl"))

# === Helper function to safely transform
def safe_transform(encoder, value, feature_name):
    value = value.title().strip()
    if value not in encoder.classes_:
        raise ValueError(
            f"{Fore.RED}🚨 Invalid value '{value}' for feature '{feature_name}'.\n"
            f"Available options: {list(encoder.classes_)}{Style.RESET_ALL}"
        )
    return encoder.transform([value])[0]

def get_user_input():
    print(f"\n{Fore.CYAN}📥 Please enter the product details for prediction:\n{Style.RESET_ALL}")

    material = input(f"Enter material {list(material_enc.classes_)}: ")
    weight = float(input("Enter weight (kg): "))
    transport = input(f"Enter transport method {list(transport_enc.classes_)}: ")
    recyclability = input(f"Enter recyclability {list(recyclability_enc.classes_)}: ")
    origin = input(f"Enter origin {list(origin_enc.classes_)}: ")

    return {
        "material": material,
        "weight": weight,
        "transport": transport,
        "recyclability": recyclability,
        "origin": origin
    }

def main():
    try:
        new_item = get_user_input()

        X_new = pd.DataFrame([{
            "material_encoded": safe_transform(material_enc, new_item["material"], "material"),
            "weight": float(new_item["weight"]),
            "transport_encoded": safe_transform(transport_enc, new_item["transport"], "transport"),
            "recycle_encoded": safe_transform(recyclability_enc, new_item["recyclability"], "recyclability"),
            "origin_encoded": safe_transform(origin_enc, new_item["origin"], "origin")
        }])

        # Spinner effect
        print(f"\n{Fore.YELLOW}🧠 Predicting your eco-score...", end="")
        for _ in range(3):
            print(".", end="", flush=True)
            time.sleep(0.5)
        print(Style.RESET_ALL)

        # Predict
        dmat_new = xgb.DMatrix(X_new)
        y_pred_probs = booster.predict(dmat_new)
        y_pred_encoded = np.argmax(y_pred_probs, axis=1)[0]
        y_pred_label = label_enc.inverse_transform([y_pred_encoded])[0]

        print(f"\n{Fore.GREEN}✅ Your product's Eco-Score is: {y_pred_label}{Style.RESET_ALL}\n")

    except ValueError as e:
        print(str(e))
        print(f"{Fore.RED}❗ Please try again with correct input values.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
