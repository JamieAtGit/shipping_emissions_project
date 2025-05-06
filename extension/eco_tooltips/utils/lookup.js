// tooltip.js — Cursor-following eco tooltip

function createFloatingTooltip() {
  const tooltip = document.createElement("div");
  tooltip.className = "eco-tooltip";
  tooltip.style.position = "absolute";
  tooltip.style.pointerEvents = "none";
  tooltip.style.opacity = 0;
  document.body.appendChild(tooltip);
  return tooltip;
}

function guessMaterialFromCategory(title) {
  const lower = title.toLowerCase();
  if (lower.includes("headphones") || lower.includes("earbuds")) return "plastic";
  if (lower.includes("phone case") || lower.includes("cover")) return "polycarbonate";
  if (lower.includes("laptop") || lower.includes("notebook")) return "aluminum";
  if (lower.includes("bottle") || lower.includes("thermos")) return "steel";
  if (lower.includes("jacket") || lower.includes("coat")) return "polyester";
  if (lower.includes("shoes") || lower.includes("trainers")) return "rubber";
  return null;
}

// ✅ Add this helper before enhanceTooltips()
window.loadMaterialInsights = async function () {
  try {
    const res = await fetch(chrome.runtime.getURL('material_insights.json'));
    return await res.json();
  } catch (e) {
    console.error("❌ Failed to load insights:", e);
    return {};
  }
};

async function enhanceTooltips() {
  const products = document.querySelectorAll("h2.a-size-mini a.a-link-normal");
  if (!products.length) return;

  const tooltip = createFloatingTooltip();
  const insights = await window.loadMaterialInsights();

  products.forEach((el) => {
    const title = el.textContent.toLowerCase();

    let matched = null;
    for (const key in insights) {
      const regex = new RegExp(`\\b${key}\\b`, "i");
      if (regex.test(title)) {
        matched = { ...insights[key], name: key };
        break;
      }
    }

    if (!matched) return;

    el.addEventListener("mousemove", (e) => {
      tooltip.style.left = `${e.pageX + 15}px`;
      tooltip.style.top = `${e.pageY + 10}px`;
      const confidence = matched.confidence || 75;

      tooltip.innerHTML = `
        <div><strong>🧬 Material: ${matched.name || "Unknown"}</strong></div>
        <div><strong>${matched.impact || "Eco Score"}</strong></div>
        <div>${matched.summary || "No summary available."}</div>
        <div>${matched.recyclable === true ? "♻️ Recyclable" : matched.recyclable === false ? "🚯 Not recyclable" : ""}</div>
        <div style="margin-top: 6px;">
          <div style="font-size: 12px; margin-bottom: 2px;">Confidence:</div>
          <div style="height: 6px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
            <div style="width: ${confidence}%; background: #4ade80; height: 100%;"></div>
          </div>
        </div>
        <div style="margin-top: 8px;">
          <a href="https://yourdomain.com/insights" target="_blank" style="font-size: 12px; color: #2563eb;">Learn more ↗</a>
        </div>
      `;
      tooltip.style.opacity = 1;
    });

    el.addEventListener("mouseleave", () => {
      tooltip.style.opacity = 0;
    });
  });
}

window.ecoLookup = async function (title, materialHint) {
  const getURL = typeof chrome !== "undefined" && chrome.runtime?.getURL
    ? chrome.runtime.getURL
    : (path) => path;

  const res = await fetch(getURL("material_insights.json"));
  const data = await res.json();

  // Normalize
  title = (title || "").toLowerCase();
  materialHint = (materialHint || "")
    .replace(/[\u200E\u200F\u202A-\u202E]/g, "") // Strip hidden Unicode chars
    .trim()
    .toLowerCase();

  console.log("🔍 Looking up title:", title);
  if (materialHint) console.log("🧪 Material hint:", materialHint);

  // Priority 1: Exact match from materialHint
  for (const key in data) {
    if (materialHint.includes(key)) {
      console.log("✅ Matched from material hint:", key);
      return { ...data[key], name: key };
    }
  }

  // Priority 2: Fuzzy match from title
  let bestMatch = null;
  let confidence = 0;

  for (const key in data) {
    const regex = new RegExp(`\\b${key}\\b`, "i");
    if (regex.test(title)) {
      const matchCount = title.split(key).length - 1;
      if (matchCount > confidence) {
        bestMatch = { ...data[key], name: key };
        confidence = matchCount;
      }
    }
  }

  if (bestMatch) {
    console.log("🔍 Fuzzy matched from title:", bestMatch);
    return bestMatch;
  }

  // Priority 3: Guess from category
  const fallback = guessMaterialFromCategory(title);
  if (fallback && data[fallback]) {
    console.log("🔁 Using fallback category material:", fallback);
    return { ...data[fallback], name: fallback };
  }

  return null;
};
