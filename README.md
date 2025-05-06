# Cleaned Repo ✅

# 🌎 Eco Impact Estimator Project

This project predicts and analyzes the environmental impact of consumer products using:
- 🧠 Machine learning (XGBoost)
- 🔎 Real-time Amazon product scraping
- 🌐 A Chrome extension overlay
- 🖥️ A web-based interface for users to explore and test predictions

---

## 📁 Project Structure

| Folder | Purpose |
|--------|---------|
| `ml_model/`          | Training, tuning, and storing ML models (XGBoost) |
| `Website/`           | React + Tailwind web frontend (Home, Learn, Predict pages) |
| `Extension/`         | Chrome extension for eco impact overlays |
| `ReactPopup/`        | Popup-based carbon estimator (optional) |
| `static/`            | Shared assets like icons, styles, etc. |
| `selenium_profile/`  | Customized scraping setup using Selenium |
| `emissions-proxy/`   | Optional proxy server (if needed for APIs) |

---

## 🚀 Installation & Setup

### 🔧 Backend (Flask API + ML Models)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd DSProject/

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask server
python app.py
```

### 🌐 Frontend (React Website)

```bash
cd Website/
npm install       # Install dependencies
npm run dev       # Run in development mode
npm run build     # Build for production (outputs to /dist/)
```

### 🧩 Chrome Extension

- Load `Extension/` as an unpacked extension (Dev Mode ON).
- Optional: Load `ReactPopup/dist/` for popup UI overlay.

---

## ⚙️ Environment Variables

In a `.env` file (optional):
```
FLASK_ENV=development
PORT=5000
SECRET_KEY=your_secret_key_here
```

---

## 🧠 Machine Learning Models

- Trained models live in `ml_model/` (`eco_model.pkl`, `xgb_model_optimized.json`)
- Data in `eco_dataset.csv`, `real_scraped_dataset.csv`
- To retrain:
  ```bash
  python train_model.py
  # or
  python train_xgboost.py
  ```

---

## 📡 API Route Table

| Endpoint               | Method | Description |
|------------------------|--------|-------------|
| `/api/predict`         | POST   | Predict eco score from product data |
| `/api/batch_predict`   | POST   | Predict scores in bulk (CSV/JSON) |
| `/api/feedback`        | POST   | Log user feedback on predictions |
| `/api/products`        | GET    | Fetch stored product predictions |
| `/api/scrape`          | POST   | (Optional) Trigger live scraping |

---

## 📷 Screenshots / GIFs

📌 *To be added* — showing Chrome extension tooltip, SHAP explanations, and web prediction flow.

---

## 🧪 Testing

- Unit tests planned for core ML + API logic
- Test commands (planned) will live in `/tests/`

---

## 🧱 Architecture Diagram

📌 *To be added to both README and dissertation:*  
A high-level system overview including:
- Scraper ➝ Cleaner ➝ Predictor ➝ Web/Extension

---

## ✍️ Future Enhancements

- [ ] Let users challenge or refine a prediction
- [ ] CI/CD GitHub Action (auto-test & deploy)
- [ ] Docker setup (optional)

---

## 👤 Author

Created by Jamie Young — Dissertation project for The University of The West of England, 2025.
# DSProject
