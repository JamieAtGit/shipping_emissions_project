import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from xgboost import XGBClassifier
from collections import Counter
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE

# === Paths ===
script_dir = os.path.dirname(__file__)
model_dir = os.path.join(script_dir)
encoders_dir = os.path.join(model_dir, "xgb_encoders")
os.makedirs(encoders_dir, exist_ok=True)

csv_path = os.path.join(model_dir, "eco_dataset.csv")
model_path = os.path.join(model_dir, "xgb_model.json")
metrics_path = os.path.join(model_dir, "xgb_metrics.json")

# === Load dataset ===
cols = ["title", "material", "weight", "transport", "recyclability", "true_eco_score", "co2_emissions", "origin"]
df = pd.read_csv(csv_path, header=None, names=cols, quotechar='"')
df = df[df["true_eco_score"].isin(["A+", "A", "B", "C", "D", "E", "F"])].dropna()

# === Clean & encode ===
for col in ["material", "transport", "recyclability", "origin"]:
    df[col] = df[col].astype(str).str.strip().str.title()

df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
df.dropna(subset=["weight"], inplace=True)
df["weight_log"] = np.log1p(df["weight"])
df["weight_bin"] = pd.cut(df["weight"], bins=[0, 0.5, 2, 10, 100], labels=[0, 1, 2, 3])

# === Feature interactions ===
df["material_transport"] = df["material"] + "_" + df["transport"]
df["origin_recycle"] = df["origin"] + "_" + df["recyclability"]

# === Encode ===
encoders = {
    'material': LabelEncoder(),
    'transport': LabelEncoder(),
    'recyclability': LabelEncoder(),
    'origin': LabelEncoder(),
    'weight_bin': LabelEncoder(),
    'material_transport': LabelEncoder(),
    'origin_recycle': LabelEncoder(),
    'label': LabelEncoder()
}

for key, encoder in encoders.items():
    col = "true_eco_score" if key == "label" else key
    df[f"{key}_encoded"] = encoder.fit_transform(df[col].astype(str))

# === Features & target ===
X = df[[ 
    "material_encoded", "transport_encoded", "recyclability_encoded", "origin_encoded",
    "weight_log", "weight_bin_encoded", "material_transport_encoded", "origin_recycle_encoded"
]]
y = df["label_encoded"]

# === Balance ===
X_bal, y_bal = SMOTE(random_state=42).fit_resample(X, y)

# === Split ===
X_train, X_test, y_train, y_test = train_test_split(X_bal, y_bal, test_size=0.2, random_state=42, stratify=y_bal)

# === Class weights ===
counter = Counter(y_train)
total = sum(counter.values())
weights = {k: total / v for k, v in counter.items()}
sample_weights = [weights[i] for i in y_train]

# === Hyperparameter tuning ===
base_model = XGBClassifier(
    use_label_encoder=False,
    eval_metric="mlogloss",
    verbosity=0
)

param_grid = {
    "n_estimators": [200, 300, 400],
    "max_depth": [6, 7, 8],
    "learning_rate": [0.05, 0.08, 0.1],
    "subsample": [0.7, 0.85, 1.0],
    "colsample_bytree": [0.7, 0.85, 1.0]
}

search = RandomizedSearchCV(base_model, param_grid, scoring="f1_macro", n_iter=10, cv=3, verbose=1)
search.fit(X_train, y_train, sample_weight=sample_weights)

model = search.best_estimator_

# === Evaluation ===
y_pred = model.predict(X_test)
acc = model.score(X_test, y_test)
f1 = f1_score(y_test, y_pred, average="macro")
report = classification_report(y_test, y_pred, target_names=encoders["label"].classes_, output_dict=True)

print("✅ Accuracy:", acc)
print(classification_report(y_test, y_pred, target_names=encoders["label"].classes_))

# === Save model ===
model.save_model(model_path)

# === Save encoders ===
for name, encoder in encoders.items():
    joblib.dump(encoder, os.path.join(encoders_dir, f"{name}_encoder.pkl"))

# === Feature importance chart ===
plt.figure(figsize=(6, 4))
plt.barh(X.columns, model.feature_importances_)
plt.title("📊 XGBoost Feature Importance")
plt.tight_layout()
plt.savefig(os.path.join(model_dir, "xgb_feature_importance.png"))
plt.close()

# === Save metrics ===
metrics = {
    "accuracy": round(acc, 4),
    "f1_score": round(f1, 4),
    "labels": list(encoders["label"].classes_),
    "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    "per_class_f1": [round(report[label]["f1-score"], 4) for label in encoders["label"].classes_]
}

with open(metrics_path, "w") as f:
    json.dump(metrics, f, indent=2)

print("✅ All done! Model, encoders, and metrics saved.")
