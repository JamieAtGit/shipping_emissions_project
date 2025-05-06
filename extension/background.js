chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "FETCH_ECO_INSIGHT") {
      const { href } = request.payload;
  
      fetch("http://localhost:5000/estimate_emissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amazon_url: href,
          include_packaging: true
        })
      })
        .then((res) => res.json())
        .then((json) => {
          const a = json.data?.attributes || {};
          sendResponse({
            impact: a.eco_score_ml || "Unknown",
            summary: `CO₂: ${a.carbon_kg ?? "?"}kg, Material: ${a.material_type || "N/A"}`,
            recyclable: a.recyclability === "High"
              ? true
              : a.recyclability === "Low"
              ? false
              : null
          });
        })
        .catch((err) => {
          console.error("API fetch error:", err);
          sendResponse({
            impact: "Unknown",
            summary: "No insight found.",
            recyclable: null
          });
        });
  
      return true; // keep message channel open for async reply
    }
  });
  