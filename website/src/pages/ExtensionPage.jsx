import React from "react";
import Layout from "../components/Layout";

export default function ExtensionPage() {
  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-6 text-green-700">🧩 Install the EcoMate Extension</h1>

        <p className="mb-4 text-lg">
          Boost your shopping awareness with our Chrome extension! Predict eco-scores, view material impacts, and estimate emissions instantly as you browse.
        </p>

        <a
          href="https://example.com/extension-download.zip"
          download
          className="inline-block bg-green-600 text-white px-6 py-3 rounded shadow hover:bg-green-700 transition"
        >
          ⬇️ Download Extension
        </a>

        <div className="mt-8">
          <h2 className="text-2xl font-semibold mb-2">✨ What You'll Get:</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>🧠 Automatic eco score predictions as you browse products</li>
            <li>♻️ Detailed material tooltips with environmental insights</li>
            <li>📊 Emissions estimator based on weight and transport type</li>
            <li>🧪 Data backed by machine learning and verified sources</li>
          </ul>
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-medium mb-2">📷 Sneak Peek</h2>
          <img
            src="/extension-preview.png"
            alt="Preview of the EcoMate extension on Amazon"
            className="rounded shadow-md"
          />
        </div>

        <div className="mt-10">
          <h2 className="text-xl font-medium mb-2">🛠 How to Install</h2>
          <ol className="list-decimal list-inside space-y-2">
            <li>Unzip the downloaded extension file.</li>
            <li>Open Chrome and go to <code>chrome://extensions</code>.</li>
            <li>Enable "Developer mode" in the top-right corner.</li>
            <li>Click "Load unpacked" and select the unzipped folder.</li>
            <li>Visit any shopping site and see EcoMate in action!</li>
          </ol>
        </div>

        <div className="mt-10 text-sm text-gray-500">
          Need help? Contact us at <a href="mailto:support@ecomate.app" className="underline">support@ecomate.app</a>
        </div>
      </div>
    </Layout>
  );
}
