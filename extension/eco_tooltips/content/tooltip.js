function createTooltip(html) {
  const tooltip = document.createElement("div");
  tooltip.className = "eco-tooltip";
  tooltip.innerHTML = html;
  document.body.appendChild(tooltip);
  return tooltip;
}

function attachTooltipEvents(target, html) {
  const tooltip = createTooltip(html);
  target.style.borderBottom = "2px dotted green";
  target.addEventListener("mouseenter", () => {
    const rect = target.getBoundingClientRect();
    tooltip.style.top = `${rect.bottom + window.scrollY + 10}px`;
    tooltip.style.left = `${rect.left + window.scrollX}px`;
    tooltip.style.opacity = 1;
    console.log("🟢 Hovering:", html);
  });

  target.addEventListener("mouseleave", () => {
    tooltip.style.opacity = 0;
  });
}

function extractMaterialFromDetailPage() {
  const labels = document.querySelectorAll("th, span.a-text-bold");
  for (const label of labels) {
    const text = label.innerText.trim().toLowerCase();
    if (text.includes("material")) {
      const valueEl = label.closest("tr")?.querySelector("td") ||
                      label.parentElement?.nextElementSibling;
      if (valueEl) {
        const val = valueEl.innerText.trim().toLowerCase();
        if (val && val !== "material") {
          console.log("✅ Found material in product page:", val);
          return val;
        } else {
          console.warn("⚠️ Matched 'material' but no usable value:", val);
        }
      }
    }
  }
  console.warn("⚠️ No material found in detail page.");
  return null;
}


function extractMaterialFromTile(tile) {
  const text = tile.closest("div")?.innerText || "";
  const match = text.match(/Material Type[:\s]*([A-Za-z,\s]+)/i);
  if (match) {
    const material = match[1].trim().toLowerCase();
    console.log("✅ Found material in tile:", material);
    return material;
  }
  return null;
}

function showTooltipFor(target, info) {
  if (!info || typeof info !== "object") {
    console.warn("⚠️ Skipping tooltip — no info provided.");
    return;
  }

  const emoji = info.impact === "High" ? "🔥"
              : info.impact === "Moderate" ? "⚠️"
              : info.impact === "Low" ? "🌱"
              : "❓";

  const recycle = info.recyclable === true ? "♻️ Recyclable"
                   : info.recyclable === false ? "🚯 Not recyclable"
                   : "";

  // Add the title (if available) into the tooltip content
  const html = `
    <strong>🧬 Material: ${info.name || "Unknown"}</strong><br/>
    <strong>${emoji} ${info.impact || "Unknown"} Impact</strong><br/>
    <p>${info.summary || "No summary available."}</p>
    <p style="margin-top: 4px;"><em>${recycle}</em></p>
  `;

  attachTooltipEvents(target, html);
}

async function enhanceTooltips() {
  console.log("✅ Tooltip script running");

  const isProductDetail = document.querySelector("#productTitle") !== null;

  if (isProductDetail) {
    const titleEl = document.querySelector("#productTitle");
    console.log("🧩 Found titleEl:", titleEl);
    if (!titleEl || titleEl.dataset.tooltipAttached) return;

    titleEl.dataset.tooltipAttached = "true";
    const title = titleEl.textContent.trim();
    let materialHint = extractMaterialFromDetailPage();

    console.log("🧪 Product Page Title:", title);

    // Fallback 1: Try guessing material from title
    if (!materialHint) {
      const materialList = Object.keys(window.materialInsights || {});
      const titleMatch = materialList.find(mat => titleLower.includes(mat));

      if (titleMatch) {
        materialHint = titleMatch[1].toLowerCase();
        console.log("🪵 Fallback from title:", materialHint);
      }
    }

    // Fallback 2: Try guessing material from product description
    if (!materialHint) {
      const descEl = document.querySelector("#productDescription");
      const descText = descEl?.innerText || "";
      const descMatch = descText.match(/\b(aluminum|plastic|metal|wood|steel|rubber|polycarbonate|carbon fiber)\b/i);
      if (descMatch) {
        materialHint = descMatch[1].toLowerCase();
        console.log("📜 Fallback from description:", materialHint);
      }
    }

    if (!materialHint) {
      console.warn("❓ No material found — using 'unknown'");
      materialHint = "unknown";
    }

    console.log("🧪 Final Material Hint:", materialHint);

    const info = await window.ecoLookup(title, materialHint);

    showTooltipFor(titleEl, info || {
      impact: "Unknown",
      summary: "No insight found.",
      recyclable: null
    });

  } else {
    let tiles = Array.from(document.querySelectorAll(
      "h2 span, span.a-text-normal, div.puisg-title span, h2.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2 span"
    )).filter(el => el.textContent.length > 10 && !el.dataset.tooltipAttached);
    
    console.log("✅ Product tiles found:", tiles.length);

    for (const tile of tiles) {
      tile.dataset.tooltipAttached = "true";
      const title = tile.textContent.trim();
      const materialHint = extractMaterialFromTile(tile);
      const info = await window.ecoLookup(title, materialHint);
      showTooltipFor(tile, info);
    }
  }
}




// ⏱️ Debounced observer to prevent overload
let lastEnhanceRun = 0;
const DEBOUNCE_MS = 3000;

window.addEventListener("load", () => {
  setTimeout(() => {
    enhanceTooltips();
  }, 1500);
});

const observer = new MutationObserver(() => {
  const now = Date.now();
  if (now - lastEnhanceRun > DEBOUNCE_MS) {
    lastEnhanceRun = now;
    enhanceTooltips();
  }
});
observer.observe(document.body, { childList: true, subtree: true });
