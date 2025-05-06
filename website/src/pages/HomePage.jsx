import React, { useState } from "react";
import { Link } from "react-router-dom";
import PaperPlaneTrail from "../components/PaperPlaneTrail";
import MLvsDEFRAChart from "../components/MLvsDEFRAChart";
import InsightsDashboard from "../components/InsightsDashboard";
import EcoLogTable from "../components/EcoLogTable";


export default function HomePage() {
  const [url, setUrl] = useState("");
  const [postcode, setPostcode] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [showML, setShowML] = useState(true);
  const hasAttributes = result && result.attributes;


  const handleSearch = async () => {
    setLoading(true);
    setError("");
    setResult(null); // ✅ reset result correctly here

    try {
      const res = await fetch("http://localhost:5000/estimate_emissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amazon_url: url,
          postcode: postcode || "SW1A 1AA",
          include_packaging: true,
        }),
      });

      const data = await res.json();
      console.log("📦 API response from /estimate_emissions:", data);

      if (!res.ok) throw new Error(data.error || "Unknown error");

      setResult(data.data); // ✅ set result after parsing JSON
    } catch (err) {
      console.error("❌ Failed to fetch emissions estimate:", err);
      setError(err.message || "Failed to contact backend.");
    } finally {
      setLoading(false);
    }
  };


  const originKm = parseFloat(hasAttributes ? result.attributes.distance_from_origin_km : 0);
  const ukKm = parseFloat(hasAttributes ? result.attributes.distance_from_uk_hub_km : 0);
  
  return (
    <div className="relative min-h-screen overflow-hidden bg-white">
      <PaperPlaneTrail />

      <div className="relative z-10 flex flex-col items-center justify-start p-6 font-sans text-gray-900">
        <header className="w-full max-w-6xl py-6 flex justify-between items-center border-b">
          <h1 className="text-2xl font-bold text-green-700">🌿 Impact Tracker</h1>
          <nav className="space-x-6 text-gray-600 text-sm">
            <Link to="/">Home</Link>
            <Link to="/learn">Learn</Link>
            <Link to="/predict">Predict</Link>
            <Link to="/login">Login</Link>
            <Link to="/extension">Extension</Link>
          </nav>
        </header>

        <section className="text-center mt-20 mb-10">
          <h2 className="text-3xl font-semibold mb-4">Ready to learn about your products?</h2>
          <p className="text-gray-500 max-w-lg mx-auto">
            Enter an Amazon product URL and postcode to reveal its environmental footprint.
          </p>
        </section>

        <div className="flex flex-col sm:flex-row gap-3 w-full max-w-2xl mb-10">
          <input
            type="text"
            placeholder="Amazon product URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="border border-gray-300 rounded px-4 py-2 flex-1 shadow-sm"
          />
          <input
            type="text"
            placeholder="Postcode (optional)"
            value={postcode}
            onChange={(e) => setPostcode(e.target.value)}
            className="border border-gray-300 rounded px-4 py-2 w-full sm:w-48 shadow-sm"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !url}
            className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition disabled:opacity-50"
          >
            {loading ? "Loading..." : "Search"}
          </button>
        </div>

        {error && <p className="text-red-500 mb-4">{error}</p>}

        {result && (
          <>
            <div className="mb-4">
              <button
                onClick={() => setShowML(!showML)}
                className="px-4 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
              >
                {showML ? "Switch to DEFRA" : "Switch to ML"}
              </button>
            </div>

            <div className="bg-gray-50 border rounded-xl p-6 w-full max-w-2xl shadow-lg text-left space-y-2 mb-16">
              <h3 className="text-xl font-semibold mb-3">🌍 Product Impact Summary</h3>
              <p><strong>Product:</strong> {result.title}</p>
              <p><strong>Weight:</strong> {hasAttributes && result.attributes.raw_product_weight_kg} kg</p>

              <p><strong>+ Packaging:</strong> {result.attributes.weight_kg} kg</p>
              <p><strong>Origin:</strong> {result.attributes.origin}</p>
              <p>
                <strong>Eco Score:</strong> {result.attributes.eco_score_ml}
                <span className="text-yellow-500 ml-2">
                  ({result.attributes.eco_score_confidence || "N/A"} confident)
                </span>
              </p>
              <p><strong>Material Type:</strong> {result.attributes.material_type}</p>
              <p><strong>Transport Mode:</strong> {result.attributes.transport_mode}</p>
              <p><strong>Recyclability:</strong> {result.attributes.recyclability}</p>
              <p><strong>Carbon Emissions:</strong> {result.attributes.carbon_kg} kg CO₂</p>
              <p className="text-sm text-gray-700">
                <strong>🌳 Offset Equivalent:</strong>{" "}
                It would take{" "}
                <span className="font-semibold text-green-700">
                  {result.attributes.trees_to_offset} tree
                  {result.attributes.trees_to_offset > 1 ? "s" : ""}
                </span>{" "}
              </p>

              <p><strong>Intl Distance:</strong> {
                Number.isFinite(originKm) ? `${originKm.toFixed(1)} km` : "❌ Invalid"
              }</p>

              <p><strong>UK Distance:</strong> {
                Number.isFinite(ukKm) ? `${ukKm.toFixed(1)} km` : "❌ Invalid"
              }</p>


              <MLvsDEFRAChart
                showML={showML}
                mlScore={result.attributes.eco_score_ml}
                defraCarbonKg={result.attributes.carbon_kg}
                mlCarbonKg={result.attributes.ml_carbon_kg}
              />
            </div>
          </>
        )}

        <InsightsDashboard />
        <h3 className="text-xl font-bold mt-10 mb-4">📋 Explore Logged Product Estimates</h3>
        <EcoLogTable />

        <footer className="w-full border-t py-4 text-sm text-center text-gray-400 mt-auto">
          © 2025 EcoTrack. Built with 💚 for a greener future.
        </footer>
      </div>
    </div>
  );
}
