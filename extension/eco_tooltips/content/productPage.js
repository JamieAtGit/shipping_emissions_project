(async function () {
  const titleElement = document.getElementById("productTitle");
  if (!titleElement) return;

  const titleText = titleElement.textContent.trim();
  const info = (await window.ecoLookup?.(titleText)) || {
    impact: "Unknown",
    summary: "No environmental insights found for this product.",
    recyclable: null
  };

  let impactEmoji = "❓";
  if (info.impact === "High") impactEmoji = "🔥 High Impact";
  else if (info.impact === "Moderate") impactEmoji = "⚠️ Moderate Impact";
  else if (info.impact === "Low") impactEmoji = "🌱 Low Impact";

  let recycleNote = "";
  if (info.recyclable === true) recycleNote = "♻️ Recyclable";
  else if (info.recyclable === false) recycleNote = "🚯 Not recyclable";

  const panel = document.createElement("div");
  panel.className = "eco-panel";
  panel.style.marginTop = "12px";
  panel.style.padding = "12px";
  panel.style.backgroundColor = "#f4f4f4";
  panel.style.borderLeft = "5px solid #4caf50";
  panel.style.fontFamily = "Arial";
  panel.style.fontSize = "14px";
  panel.innerHTML = `
    <strong>🌍 Environmental Snapshot</strong><br/>
    ${impactEmoji} <strong>Impact Level:</strong> ${info.impact}<br/>
    <strong>Summary:</strong> ${info.summary}<br/>
    <strong>Recyclability:</strong> ${recycleNote}<br/>
    <em style="font-size: 12px;">Based on product title only. Accuracy may vary.</em>
    <br/><br/>
    <label for="transport-select"><strong>Choose Transport Mode:</strong></label><br/>
  `;

  // === Transport dropdown
  const transportSelect = document.createElement("select");
  transportSelect.id = "transport-select";
  ["Air", "Ship", "Land"].forEach(mode => {
    const opt = document.createElement("option");
    opt.value = mode;
    opt.textContent = mode;
    transportSelect.appendChild(opt);
  });

  // === Estimate button
  const button = document.createElement("button");
  button.id = "estimate-button";
  button.textContent = "Estimate Shipping Emissions";
  button.style.marginTop = "10px";
  button.style.marginLeft = "10px";
  button.style.padding = "6px 12px";
  button.style.background = "#4caf50";
  button.style.color = "#fff";
  button.style.border = "none";
  button.style.borderRadius = "4px";
  button.style.cursor = "pointer";

  // === Results container
  const resultContainer = document.createElement("div");
  resultContainer.id = "emission-result";
  resultContainer.style.marginTop = "10px";

  // === On-click logic
  button.onclick = async () => {
    const selectedTransport = transportSelect.value || "Land";
    console.log("🚚 Selected transport sent to backend:", selectedTransport);

    const key = `emissions_${window.location.href}_${selectedTransport}`;
    const cached = localStorage.getItem(key);
    if (cached) {
      resultContainer.innerHTML = renderResult(JSON.parse(cached));
      return;
    }

    button.textContent = "Estimating...";
    button.disabled = true;

    try {
      const res = await fetch("http://localhost:5000/estimate_emissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amazon_url: window.location.href,
          transport: selectedTransport
        })
      });

      if (!res.ok) throw new Error("Server error");

      const data = await res.json();
      localStorage.setItem(key, JSON.stringify(data));
      resultContainer.innerHTML = renderResult(data);
    } catch (err) {
      console.error("❌ Estimate failed:", err);
      if (confirm("Failed to contact backend. Try again?")) button.click();
    } finally {
      button.textContent = "Estimate Shipping Emissions";
      button.disabled = false;
    }
  };

  panel.appendChild(transportSelect);
  panel.appendChild(button);
  panel.appendChild(resultContainer);
  titleElement.insertAdjacentElement("afterend", panel);

  function renderResult(data) {
    const attr = data?.data?.attributes;
    if (!attr) return "<p style='color:red;'>No result.</p>";

    return `
      <div style="margin-top: 8px; font-size: 14px;">
        <strong>📦 Material:</strong> ${attr.material_type}<br/>
        <strong>⚖️ Weight:</strong> ${attr.weight_kg} kg<br/>
        <strong>🛣️ Distance:</strong> ${attr.intl_distance_km} km<br/>
        <strong>🌫️ CO₂ Estimate:</strong> ${attr.carbon_kg} kg<br/>
        <strong>🌲 Trees to offset:</strong> ${attr.trees_to_offset}
      </div>
    `;
  }
})();
