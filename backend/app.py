
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import joblib
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.auth import auth
import pandas as pd
from backend.services.scraper.scrape_amazon_titles  import (scrape_amazon_product_page, estimate_origin_country, resolve_brand_origin, save_brand_locations)
import csv
import re

# === Load Flask ===
app = Flask(__name__)
app.secret_key = "super-secret-key"

CORS(app, supports_credentials=True, resources={r"/*": {
    "origins": [
        "http://localhost:5173",
        "chrome-extension://pjdiihkkececfngkhihclponhkaegkda"  # extension's ID
    ],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
}})

app.register_blueprint(auth)

@app.route("/")
def index():
    return "✅ Backend running"

@app.after_request
def apply_cors(response):
    origin = request.headers.get("Origin")
    allowed = [
        "http://localhost:5173",
        "chrome-extension://pjdiihkkececfngkhihclponhkaegkda"
    ]
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


SUBMISSION_FILE = "submitted_predictions.json"


@app.route("/admin/submissions")
def get_submissions():
    if not os.path.exists(SUBMISSION_FILE):
        return jsonify([])
    with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/admin/update", methods=["POST"])
def update_submission():
    item = request.json
    with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for i, row in enumerate(data):
        if row["title"] == item["title"]:
            data[i] = item
            break
    with open(SUBMISSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return jsonify({"status": "success"})


def log_submission(product):
    path = "submitted_predictions.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    data.append(product)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
def load_material_co2_data():
    try:
        import pandas as pd
        df = pd.read_csv("ml_model/defra_material_intensity.csv")
        return {str(row["material"]).lower(): float(row["co2_per_kg"]) for _, row in df.iterrows()}
    except Exception as e:
        print(f"⚠️ Could not load CO₂ map: {e}")
        return {}

material_co2_map = load_material_co2_data()

@app.route("/predict", methods=["POST"])
def predict_eco_score():
    print("📩 /predict endpoint was hit via POST")  # debug
    try:
        data = request.get_json()
        product = {}  # ensure it's always defined
        material = normalize_feature(data.get("material"), "Other")
        weight = float(data.get("weight") or 0.0)
        # Estimate default transport from distance if none provided
        user_transport = data.get("transport")
        origin_km = float(product.get("distance_origin_to_uk", 0) or 0)

        # Heuristic fallback: choose mode by distance
        def guess_transport_by_distance(km):
            if km > 7000:
                return "Ship"
            elif km > 2000:
                return "Air"
            else:
                return "Land"

        transport = normalize_feature(user_transport or guess_transport_by_distance(origin_km), "Land")
        print(f"🚛 Final transport used: {transport} (user selected: {user_transport})")

        recyclability = normalize_feature(data.get("recyclability"), "Medium")
        origin = normalize_feature(data.get("origin"), "Other")

        # === Encode features
        material_encoded = safe_encode(material, material_encoder, "Other")
        transport_encoded = safe_encode(transport, transport_encoder, "Land")
        recycle_encoded = safe_encode(recyclability, recycle_encoder, "Medium")
        origin_encoded = safe_encode(origin, origin_encoder, "Other")

        # === Bin weight (for 6th feature)
        def bin_weight(w):
            if w < 0.5:
                return 0
            elif w < 2:
                return 1
            elif w < 10:
                return 2
            else:
                return 3

        weight_bin_encoded = bin_weight(weight)

        # === Prepare input for model
        X = [[
            material_encoded,
            weight,
            transport_encoded,
            recycle_encoded,
            origin_encoded,
            weight_bin_encoded
        ]]
        
        prediction = model.predict(X)
        decoded_score = label_encoder.inverse_transform([prediction[0]])[0]

        confidence = 0.0
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)
            confidence = round(max(proba[0]) * 100, 1)

        # === Feature Importance (optional)
        global_importance = model.feature_importances_
        local_impact = {
            "material": to_python_type(material_encoded * global_importance[0]),
            "weight": to_python_type(weight * global_importance[1]),
            "transport": to_python_type(transport_encoded * global_importance[2]),
            "recyclability": to_python_type(recycle_encoded * global_importance[3]),
            "origin": to_python_type(origin_encoded * global_importance[4]),
            "weight_bin": to_python_type(weight_bin_encoded * global_importance[5]),
        }

        # === Log the prediction
        log_submission({
            "title": data.get("title", "Manual Submission"),
            "raw_input": {
                "material": material,
                "weight": weight,
                "transport": transport,
                "recyclability": recyclability,
                "origin": origin
            },
            "predicted_label": decoded_score,
            "confidence": f"{confidence}%"
        })

        # === Return JSON response
        return jsonify({
            "predicted_label": decoded_score,
            "confidence": f"{confidence}%",
            "raw_input": {
                "material": material,
                "weight": weight,
                "transport": transport,
                "recyclability": recyclability,
                "origin": origin
            },
            "encoded_input": {
                "material": to_python_type(material_encoded),
                "weight": to_python_type(weight),
                "transport": to_python_type(transport_encoded),
                "recyclability": to_python_type(recycle_encoded),
                "origin": to_python_type(origin_encoded),
                "weight_bin": to_python_type(weight_bin_encoded)
            },
            "feature_impact": local_impact
        })

    except Exception as e:
        print(f"❌ Error in /predict: {e}")
        return jsonify({"error": str(e)}), 500


# === Load Model and Encoders ===
model_dir = "ml_model"
encoders_dir = os.path.join(model_dir, "encoders")

model = joblib.load(os.path.join(model_dir, "eco_model.pkl"))
material_encoder = joblib.load(os.path.join(encoders_dir, "material_encoder.pkl"))
transport_encoder = joblib.load(os.path.join(encoders_dir, "transport_encoder.pkl"))
recycle_encoder = joblib.load(os.path.join(encoders_dir, "recycle_encoder.pkl"))
label_encoder = joblib.load(os.path.join(encoders_dir, "label_encoder.pkl"))
origin_encoder = joblib.load(os.path.join(encoders_dir, "origin_encoder.pkl"))

valid_scores = list(label_encoder.classes_)
print("✅ Loaded label classes:", valid_scores)




@app.route("/all-model-metrics", methods=["GET"])
def get_all_model_metrics():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # backend/
        metrics_path = os.path.join(base_dir, "..", "ml_model", "metrics.json")
        xgb_path = os.path.join(base_dir, "..", "ml_model", "xgb_metrics.json")

        with open(metrics_path, "r", encoding="utf-8") as f1, open(xgb_path, "r", encoding="utf-8") as f2:
            return jsonify({
                "random_forest": json.load(f1),
                "xgboost": json.load(f2)
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/model-metrics", methods=["GET"])
def get_model_metrics():
    try:
        with open("ml_model/metrics.json", "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# === Load CO2 Map ===
def load_material_co2_data():
    try:
        df = pd.read_csv(os.path.join(model_dir, "defra_material_intensity.csv"))
        return dict(zip(df["material"], df["co2_per_kg"]))
    except Exception as e:
        print(f"⚠️ Could not load DEFRA data: {e}")
        return {}

material_co2_map = load_material_co2_data()

# === Helpers ===
def normalize_feature(value, default):
    clean = str(value or default).strip().title()
    return default if clean.lower() == "unknown" else clean

def safe_encode(value, encoder, default):
    value = normalize_feature(value, default)
    if value not in encoder.classes_:
        print(f"⚠️ '{value}' not in encoder classes. Defaulting to '{default}'.")
        value = default
    return encoder.transform([value])[0]

@app.route("/api/feature-importance")
def get_feature_importance():
    try:
        importances = model.feature_importances_
        features = ["material", "weight", "transport", "recyclability", "origin"]
        data = [{"feature": f, "importance": round(i * 100, 2)} for f, i in zip(features, importances)]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



def to_python_type(obj):
    import numpy as np
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    return obj


# === Fuzzy Matching Helpers ===
def fuzzy_match_material(material):
    material_keywords = {
        "Plastic": ["plastic", "plastics"],
        "Glass": ["glass"],
        "Aluminium": ["aluminium", "aluminum"],
        "Steel": ["steel"],
        "Paper": ["paper", "papers"],
        "Cardboard": ["cardboard", "corrugated"],
    }

    material_lower = material.lower()
    for clean, keywords in material_keywords.items():
        if any(keyword in material_lower for keyword in keywords):
            return clean
    return material

def fuzzy_match_origin(origin):
    origin_keywords = {
        "China": ["china"],
        "UK": ["uk", "united kingdom"],
        "USA": ["usa", "united states", "america"],
        "Germany": ["germany"],
        "France": ["france"],
        "Italy": ["italy"],
    }

    origin_lower = origin.lower()
    for clean, keywords in origin_keywords.items():
        if any(keyword in origin_lower for keyword in keywords):
            return clean
    return origin

@app.route("/api/eco-data", methods=["GET"])
def fetch_eco_dataset():
    try:

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, 'eco_dataset.csv')

        df = pd.read_csv(file_path)

        df = df.dropna(subset=["material", "true_eco_score", "co2_emissions"])
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        print(f"❌ Failed to return eco dataset: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/insights", methods=["GET"])
def insights_dashboard():
    try:
        # Load the logged data
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), "eco_dataset.csv"))
        df = df.dropna(subset=["material", "true_eco_score", "co2_emissions"])  # Clean

        # Keep only the needed fields
        insights = df[["material", "true_eco_score", "co2_emissions"]]
        insights = insights.head(1000)  # Limit for frontend performance

        return jsonify(insights.to_dict(orient="records"))
    except Exception as e:
        print(f"❌ Failed to serve insights: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    try:
        data = request.get_json()
        feedback_dir = os.path.join("ml_model", "user_feedback.json")
        print("Received feedback:", data)
        # Append to file
        import json
        existing = []
        if os.path.exists(feedback_dir):
            with open(feedback_dir, "r") as f:
                existing = json.load(f)

        existing.append(data)

        with open(feedback_dir, "w") as f:
            json.dump(existing, f, indent=2)

        return jsonify({"message": "✅ Feedback saved!"}), 200

    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/estimate_emissions", methods=["POST", "OPTIONS"])
def estimate_emissions():
    if request.method == "OPTIONS":
        # This is a preflight request (CORS)
        return '', 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON in request"}), 400

    # ... your existing logic ...

    try:
        data = request.get_json()
        url = data.get("amazon_url")
        user_transport = data.get("transport")  # User's selected mode like "Air"
        include_packaging = data.get("include_packaging", True)

        # Default empty product
        product = {}

        # Use mock product if scraping is skipped
        if url:
            print("🌐 Scraping real product:", url)
            product = scrape_amazon_product_page(url)
            if not product:
                return jsonify({"error": "Failed to scrape product"}), 500

            title = product.get("title", "Amazon Product")
            material = normalize_feature(product.get("material_type"), "Other")
            transport = normalize_feature(data.get("transport"), "Land")
            print("🛫 Transport received from frontend:", data.get("transport"))



            recyclability = normalize_feature(product.get("recyclability"), "Medium")

            origin = normalize_feature(
                product.get("brand_estimated_origin") or product.get("origin"), 
                "Other"
            )

            if origin in ["Unknown", "Other", None, ""] and title:
                guessed = estimate_origin_country(title)
                if guessed and guessed.lower() != "other":
                    print(f"🧠 Fallback origin estimate from title: {guessed}")
                    origin = guessed
                else:
                    print(f"🔒 Skipped fallback — origin already trusted: {origin}")

            dimensions = product.get("dimensions_cm")
            raw_weight = product.get("raw_product_weight_kg")
            estimated_weight = product.get("estimated_weight_kg")

            try:
                weight = float(raw_weight if raw_weight not in [None, 0] else estimated_weight if estimated_weight not in [None, 0] else 0.5)
            except:
                weight = 0.5


            if include_packaging:
                weight *= 1.05

            print(f"✅ Final product weight used: {weight:.2f} kg (5% packaging included)")


            raw_weight = product.get("raw_product_weight_kg")
            estimated_weight = product.get("estimated_weight_kg")
            weight = float(raw_weight or estimated_weight or 0.5)
            if include_packaging:
                weight *= 1.05

            try:
                weight = float(raw_weight or estimated_weight or 0.5)
            except:
                weight = 0.5

            if include_packaging:
                weight *= 1.05

            print(f"✅ Final product weight used: {weight:.2f} kg (5% packaging included)")


        else:
            title = data.get("title", "Manual Product")
            material = normalize_feature(data.get("material"), "Other")
            transport = normalize_feature(data.get("transport"), "Land")
            print("🛫 Transport received from frontend:", data.get("transport"))

            recyclability = normalize_feature(data.get("recyclability"), "Medium")
            origin = normalize_feature(data.get("origin"), "Other")
            dimensions = None

            try:
                weight = float(data.get("weight") or 0.5)
            except:
                weight = 0.5

            if include_packaging:
                weight *= 1.05

            print(f"✅ Final manual product weight used: {weight} kg")

        # Fuzzy material and origin mappings
        material = fuzzy_match_material(material)
        origin = fuzzy_match_origin(origin)

        # Calculate carbon
        carbon_kg = round(weight * material_co2_map.get(material, 2.0), 2)

        X = pd.DataFrame([[ 
            safe_encode(material, material_encoder, "Other"),
            weight,
            safe_encode(transport, transport_encoder, "Land"),
            safe_encode(recyclability, recycle_encoder, "Medium"),
            safe_encode(origin, origin_encoder, "Other")
        ]], columns=[
            "material_encoded", 
            "weight", 
            "transport_encoded", 
            "recycle_encoded", 
            "origin_encoded"
        ])

        # ML prediction
        decoded_score = "C"
        confidence = 0.0
        try:
            prediction = model.predict(X)[0]
            decoded_score = label_encoder.inverse_transform([prediction])[0]
            if decoded_score not in valid_scores:
                decoded_score = "C"

            if hasattr(model, "predict_proba"):
                try:
                    proba = model.predict_proba(X)
                    print("🔍 Probabilities:", proba)
                    if proba is not None and len(proba[0]) > 0:
                        confidence = round(max(proba[0]) * 100, 1)
                except Exception as e:
                    print(f"⚠️ predict_proba failed: {e}")
        except Exception as e:
            print(f"⚠️ Prediction failed: {e}")


        # Logging
        try:
            log_path = os.path.join(model_dir, "eco_dataset.csv")
            with open(log_path, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                writer.writerow([title, material, f"{weight:.2f}", transport, recyclability, decoded_score, carbon_kg, origin])
        except Exception as log_error:
            print(f"⚠️ Logging skipped: {log_error}")
            
        # 🔒 Log only real, valid scraped entries to a separate dataset for training
        try:
            if url:  # confirms this was a scraped product
                valid_materials = list(material_encoder.classes_)
                valid_transports = list(transport_encoder.classes_)
                valid_recyclability = list(recycle_encoder.classes_)
                valid_origins = list(origin_encoder.classes_)

                if (
                    decoded_score in valid_scores and
                    material in valid_materials and
                    transport in valid_transports and
                    recyclability in valid_recyclability and
                    origin in valid_origins
                ):
                    clean_log_path = os.path.join(model_dir, "real_scraped_dataset.csv")
                    with open(clean_log_path, "a", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                        writer.writerow([title, material, f"{weight:.2f}", transport, recyclability, decoded_score, carbon_kg, origin])
                    print("✅ Logged to real_scraped_dataset.csv")
                else:
                    print("⚠️ Skipped real_scraped_dataset.csv log: one or more values are invalid.")
        except Exception as clean_log_error:
            print(f"⚠️ Logging to real_scraped_dataset.csv failed: {clean_log_error}")

        # Emojis
        emoji_map = {
            "A+": "🌍", "A": "🌿", "B": "🍃",
            "C": "🌱", "D": "⚠️", "E": "❌", "F": "💀"
        }
        origin_distance_km = float(product.get("distance_origin_to_uk", 0) or 0)
        uk_distance_km = float(product.get("distance_uk_to_user", 0) or 0)
        
        # Always create formatted strings for distances
        origin_distance_formatted = f"{origin_distance_km:.1f} km"
        uk_distance_formatted = f"{uk_distance_km:.1f} km"
        
        print(f"🎯 Formatted distances: {origin_distance_formatted}, {uk_distance_formatted}")

        return jsonify({
            "data": {
                "attributes": {
                    "eco_score_ml": f"{decoded_score} {emoji_map.get(decoded_score, '')} ({confidence}%)",
                    "eco_score_confidence": f"{confidence}%",
                    "ml_carbon_kg": round(weight * 1.2, 2),
                    "trees_to_offset": max(1, round(carbon_kg / 15)),
                    "material_type": material,
                    "weight_kg": round(weight, 2),
                    "raw_product_weight_kg": round(raw_weight or estimated_weight or 0.5, 2),
                    "transport_mode": transport,
                    "recyclability": recyclability,
                    "origin": origin,
                    "dimensions_cm": dimensions,
                    "carbon_kg": round(carbon_kg, 2),
                    
                    "distance_from_origin_km": origin_distance_km,
                    "distance_from_uk_hub_km": uk_distance_km,
                    "intl_distance_km": origin_distance_km,
                    "uk_distance_km": uk_distance_km

                },
                "title": title
            }
        })

    except Exception as e:
        print(f"❌ Uncaught error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/test_post", methods=["POST"])
def test_post():
    try:
        data = request.get_json()
        print("✅ Received test POST:", data)
        return jsonify({"message": "Success", "you_sent": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route("/health")
def health():
    return jsonify({"status": "✅ Server is up"}), 200


@app.route("/")
def home():
    return "<h2>🌍 Flask is running</h2>"

@app.route("/test")
def test():
    return "✅ Flask test OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
