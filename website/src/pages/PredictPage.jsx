import React, { useState } from "react";
import ChallengeForm from "../components/ChallengeForm";
import toast from "react-hot-toast";
import Layout from "../components/Layout";

export default function PredictPage() {
  const [form, setForm] = useState({
    title: "",
    material: "Plastic",
    weight: 1.0,
    transport: "Air",
    recyclability: "Low",
    origin: "China",
  });

  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("http://localhost:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!response.ok) throw new Error("Failed to predict");

      const data = await response.json();
      setResult(data);
      toast.success("✅ Prediction successful!");
    } catch (error) {
      console.error("Prediction error:", error);
      toast.error("❌ Failed to predict");
    }
  };

  const sendFeedback = async (vote) => {
    const feedback = {
      vote,
      title: result.raw_input?.title || "unknown",
      prediction: result.predicted_label,
      confidence: result.confidence,
      raw_input: result.raw_input,
      encoded_input: result.encoded_input,
      feature_impact: result.feature_impact,
      timestamp: new Date().toISOString(),
    };

    await fetch("http://localhost:5000/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(feedback),
    });

    toast.success("✅ Thanks for your feedback!");
  };

  return (
    <Layout>
      <div className="p-6 max-w-xl mx-auto">
        <h2 className="text-3xl font-bold text-green-700 mb-6">♻️ Eco Score Predictor</h2>

        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow space-y-4">
          <div>
            <label className="block">Product Title:</label>
            <input
              className="border p-2 w-full"
              name="title"
              type="text"
              value={form.title}
              onChange={handleChange}
              placeholder="e.g., Eco-Friendly Toothbrush"
            />
          </div>

          {[ "material", "weight", "transport", "recyclability", "origin"].map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium capitalize mb-1">{field}:</label>
              <input
                className="border rounded px-3 py-2 w-full focus:outline-none focus:ring focus:border-green-500"
                name={field}
                type={field === "weight" ? "number" : "text"}
                value={form[field]}
                onChange={handleChange}
              />
            </div>
          ))}

          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition"
          >
            🔍 Predict Score
          </button>
        </form>

        {result && (
          <div className="mt-6 p-6 bg-gray-50 border rounded shadow">
            <h3 className="text-xl font-semibold mb-2">🎯 Prediction Result</h3>
            <p className="text-lg">
              <strong>Label:</strong>{" "}
              <span className="inline-block px-2 py-1 bg-green-200 rounded text-green-800">
                {result.predicted_label}
              </span>
            </p>
            <p className="text-sm text-gray-600">Confidence: {result.confidence}</p>

            <ChallengeForm
              productId={result.raw_input?.product_id || "unknown"}
              predictedScore={result.predicted_label}
            />

            <div className="mt-4 flex items-center gap-3 text-sm">
              <span>Was this prediction helpful?</span>
              <button onClick={() => sendFeedback("up")} className="hover:scale-110 transition">👍</button>
              <button onClick={() => sendFeedback("down")} className="hover:scale-110 transition">👎</button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
