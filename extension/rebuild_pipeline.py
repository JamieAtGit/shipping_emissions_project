import sys
import os
import json
import shutil
from datetime import datetime

# --- Ensure Extension folder is on the import path ---
extension_path = os.path.dirname(__file__)
sys.path.insert(0, extension_path)

from backend.services.scraper.scrape_amazon_titles import (
    resolve_brand_origin,
    extract_weight,
    maybe_add_to_priority,
    is_high_confidence
)



# === File paths
RAW_INPUT = os.path.join(extension_path, "scraped_products_tmp.json")
CLEANED_FILE = os.path.join(extension_path, "cleaned_products.json")
PRIORITY_FILE = os.path.join(extension_path, "priority_products.json")
BRAND_LOCATIONS_FILE = os.path.join(extension_path, "brand_locations.json")
UNRECOGNIZED_FILE = os.path.join(extension_path, "unrecognized_brands.txt")
BACKUP_DIR = os.path.join(extension_path, "backup")

def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M")

def backup_file(path):
    if os.path.exists(path):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        name = os.path.basename(path)
        backup_name = f"{name}_backup_{timestamp()}"
        shutil.copy(path, os.path.join(BACKUP_DIR, backup_name))
        print(f"📦 Backed up {name} → {backup_name}")

def load_json(path, default={}):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def rebuild():
    print("🚀 Starting rebuild...\n")

    for f in [CLEANED_FILE, PRIORITY_FILE, BRAND_LOCATIONS_FILE]:
        backup_file(f)

    raw_products = load_json(RAW_INPUT, default=[])
    brand_locations = load_json(BRAND_LOCATIONS_FILE, default={})
    priority_products = load_json(PRIORITY_FILE, default={})
    cleaned_products = []

    unrecognized = set()

    for product in raw_products:
        title = product.get("title", "")
        brand = product.get("brand", title.split()[0]).lower().strip()

        country, city = resolve_brand_origin(brand, title_fallback=title)
        product["brand_estimated_origin"] = country
        product["origin_city"] = city

        if country.lower() in ["unknown", "", None]:
            unrecognized.add(brand)

        if not product.get("estimated_weight_kg"):
            fallback_weight = extract_weight(title)
            if fallback_weight:
                product["estimated_weight_kg"] = fallback_weight

        cleaned_products.append(product)
        maybe_add_to_priority(product, priority_products)

    save_json(CLEANED_FILE, cleaned_products)
    save_json(PRIORITY_FILE, priority_products)

    if unrecognized:
        with open(UNRECOGNIZED_FILE, "a", encoding="utf-8") as f:
            for brand in sorted(unrecognized):
                f.write(f"{brand}\n")
        print(f"⚠️ Logged {len(unrecognized)} unknown brands → {UNRECOGNIZED_FILE}")

    print(f"\n✅ Done! {len(cleaned_products)} cleaned | {len(priority_products)} priority products")

if __name__ == "__main__":
    rebuild()
