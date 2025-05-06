import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    f1_score
)
from sklearn.preprocessing import label_binarize
from imblearn.over_sampling import SMOTE

# === Setup paths ===
script_dir = os.path.dirname(__file__)
project_root = os.path.dirname(script_dir)
csv_path = os.path.join(script_dir, "eco_dataset.csv")                      # ← make sure this CSV exists
model_dir = os.path.join(project_root, "ml_model")
encoders_dir = os.path.join(model_dir, "encoders")
os.makedirs(encoders_dir, exist_ok=True)

# === Load and clean dataset ===
column_names = ["title", "material", "weight", "transport", "recyclability", "true_eco_score", "co2_emissions", "origin"]
df = pd.read_csv(csv_path, header=None, names=column_names, quotechar='"')
df = df[df["true_eco_score"] != "true_eco_score"]
df.dropna(subset=["material", "weight", "transport", "recyclability", "origin"], inplace=True)

for col in ["material", "transport", "recyclability", "origin", "true_eco_score"]:
    df[col] = df[col].astype(str).str.strip().str.title()

# === Encode features ===
material_encoder = LabelEncoder()
transport_encoder = LabelEncoder()
recycle_encoder = LabelEncoder()
origin_encoder = LabelEncoder()
label_encoder = LabelEncoder()

df["material_encoded"] = material_encoder.fit_transform(df["material"])
df["transport_encoded"] = transport_encoder.fit_transform(df["transport"])
df["recycle_encoded"] = recycle_encoder.fit_transform(df["recyclability"])
df["origin_encoded"] = origin_encoder.fit_transform(df["origin"])
df["label_encoded"] = label_encoder.fit_transform(df["true_eco_score"])

# === Feature Engineering ===
df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
df.dropna(subset=["weight"], inplace=True)
df["weight_log"] = np.log1p(df["weight"])
df["weight_bin"] = pd.cut(df["weight"], bins=[0, 0.5, 2, 10, 100], labels=[0, 1, 2, 3])

weight_bin_encoder = LabelEncoder()
df["weight_bin_encoded"] = weight_bin_encoder.fit_transform(df["weight_bin"].astype(str))

# === Final feature set ===
feature_cols = [
    "material_encoded",
    "transport_encoded",
    "recycle_encoded",
    "origin_encoded",
    "weight_log",
    "weight_bin_encoded"
]
X = df[feature_cols]
y = df["label_encoded"]

# === Apply SMOTE ===
sm = SMOTE(random_state=42)
X_balanced, y_balanced = sm.fit_resample(X, y)

# === Train/test split ===
X_train, X_test, y_train, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
)

# === Train model ===
model = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",
    random_state=42
)
model.fit(X_train, y_train)

# === Evaluate ===
y_pred = model.predict(X_test)
acc = model.score(X_test, y_test)
f1 = f1_score(y_test, y_pred, average="macro")
print("✅ Accuracy:", acc)
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# === Save model and encoders ===
joblib.dump(model, os.path.join(model_dir, "eco_model.pkl"))
joblib.dump(material_encoder, os.path.join(encoders_dir, "material_encoder.pkl"))
joblib.dump(transport_encoder, os.path.join(encoders_dir, "transport_encoder.pkl"))
joblib.dump(recycle_encoder, os.path.join(encoders_dir, "recycle_encoder.pkl"))
joblib.dump(origin_encoder, os.path.join(encoders_dir, "origin_encoder.pkl"))
joblib.dump(label_encoder, os.path.join(encoders_dir, "label_encoder.pkl"))
joblib.dump(weight_bin_encoder, os.path.join(encoders_dir, "weight_bin_encoder.pkl"))
print("✅ Model + encoders saved!")

# === Feature Importance Chart ===
importances = model.feature_importances_
feature_names = ["material", "transport", "recyclability", "origin", "weight_log", "weight_bin"]
plt.figure(figsize=(6, 4))
plt.barh(feature_names, importances)
plt.title("🔍 Feature Importance")
plt.tight_layout()
plt.savefig(os.path.join(model_dir, "feature_importance.png"))
plt.close()
print("✅ Saved feature importance chart.")

# === Confusion Matrix ===
cm = confusion_matrix(y_test, y_pred)
labels = label_encoder.classes_
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.xlabel("Predicted")
plt.ylabel("True Label")
plt.title("📊 Confusion Matrix")
plt.tight_layout()
plt.savefig(os.path.join(model_dir, "confusion_matrix.png"))
plt.close()
print("✅ Saved confusion matrix.")

# === ROC Curve ===
y_test_bin = label_binarize(y_test, classes=range(len(labels)))
y_score = model.predict_proba(X_test)
fpr, tpr, roc_auc = dict(), dict(), dict()
for i in range(len(labels)):
    fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_score[:, i])
    roc_auc[i] = roc_auc_score(y_test_bin[:, i], y_score[:, i])

plt.figure(figsize=(6, 5))
for i in range(len(labels)):
    plt.plot(fpr[i], tpr[i], label=f"Class {labels[i]} (AUC = {roc_auc[i]:.2f})")
plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("📈 ROC Curve (One-vs-Rest)")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(model_dir, "roc_curve.png"))
plt.close()
print("✅ Saved ROC curve.")

# === Save metrics.json ===
metrics = {
    "accuracy": round(acc, 4),
    "f1_score": round(f1, 4),
    "labels": list(labels),
    "confusion_matrix": cm.tolist()
}
with open(os.path.join(model_dir, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)
print("✅ Saved model metrics to metrics.json")
