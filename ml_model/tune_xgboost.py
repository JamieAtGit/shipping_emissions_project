import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder
import os
import joblib

# === Load dataset
script_dir = os.path.dirname(__file__)
csv_path = os.path.join(script_dir, "eco_dataset.csv")
model_dir = os.path.join(script_dir, "ml_model")
os.makedirs(model_dir, exist_ok=True)

column_names = ["title", "material", "weight", "transport", "recyclability", "true_eco_score", "co2_emissions", "origin"]
df = pd.read_csv(csv_path, header=None, names=column_names, quotechar='"')

# === Clean and preprocess
valid_scores = ["A+", "A", "B", "C", "D", "E", "F"]
df = df[df["true_eco_score"].isin(valid_scores)].dropna()

for col in ["material", "transport", "recyclability", "origin"]:
    df[col] = df[col].astype(str).str.title().str.strip()

encoders = {
    'material': LabelEncoder(),
    'transport': LabelEncoder(),
    'recyclability': LabelEncoder(),
    'origin': LabelEncoder(),
    'label': LabelEncoder()
}

# Encode features
df["material_encoded"] = encoders['material'].fit_transform(df["material"])
df["transport_encoded"] = encoders['transport'].fit_transform(df["transport"])
df["recycle_encoded"] = encoders['recyclability'].fit_transform(df["recyclability"])
df["origin_encoded"] = encoders['origin'].fit_transform(df["origin"])
df["label_encoded"] = encoders['label'].fit_transform(df["true_eco_score"])

# Features and target
X = df[["material_encoded", "weight", "transport_encoded", "recycle_encoded", "origin_encoded"]].astype(float)
y = pd.Categorical(df["label_encoded"], categories=range(len(encoders['label'].classes_))).codes

# === Train/Test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Setup XGBoost Classifier
from xgboost import XGBClassifier

model = XGBClassifier(
    objective="multi:softprob",
    num_class=len(np.unique(y)),
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42
)

# === Define parameter grid for GridSearch
param_grid = {
    'max_depth': [3, 5, 7],
    'n_estimators': [50, 100, 150],
    'learning_rate': [0.01, 0.1, 0.2]
}

# === GridSearchCV
grid_search = GridSearchCV(
    estimator=model,
    param_grid=param_grid,
    scoring='accuracy',
    cv=3,
    verbose=1,
    n_jobs=-1
)

print("🔎 Running GridSearchCV... this might take a few minutes.")
grid_search.fit(X_train, y_train)

print("\n✅ Best Parameters Found:", grid_search.best_params_)
print(f"✅ Best CV Score: {grid_search.best_score_:.4f}")

# === Save best model
best_model = grid_search.best_estimator_
best_model.save_model(os.path.join(model_dir, "xgb_model_optimized.json"))
print(f"✅ Best model saved at {os.path.join(model_dir, 'xgb_model_optimized.json')}")

# === Save updated encoders as well
encoders_dir = os.path.join(model_dir, "xgb_encoders")
os.makedirs(encoders_dir, exist_ok=True)
for name, encoder in encoders.items():
    joblib.dump(encoder, os.path.join(encoders_dir, f"{name}_encoder.pkl"))

print("✅ Encoders re-saved!")
