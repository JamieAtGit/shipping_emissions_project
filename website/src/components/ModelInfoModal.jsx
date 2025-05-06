import React, { useEffect, useState } from "react";

export default function ModelInfoModal({ isOpen, onClose }) {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetch("https://eco-backend-m26q.onrender.com/all-model-metrics")
        .then((res) => res.json())
        .then((data) => {
          if (
            data.error ||
            !data.random_forest ||
            !data.xgboost
          ) {
            setError(true);
          } else {
            setMetrics(data);
          }
        })
        .catch(() => setError(true));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex justify-center items-center">
      <div className="bg-white p-6 max-w-3xl rounded-xl shadow-lg relative">
        <button
          className="absolute top-2 right-3 text-gray-600 hover:text-black"
          onClick={onClose}
        >
          ✖
        </button>

        <h2 className="text-2xl font-semibold mb-4">🔬 About the Models</h2>

        {error ? (
          <p className="text-red-500 text-sm">❌ Failed to load model comparison.</p>
        ) : !metrics ? (
          <p className="text-sm text-gray-500">Loading model metrics...</p>
        ) : (
          <>
            <table className="table-auto w-full text-sm mb-6">
              <thead>
                <tr>
                  <th className="text-left">Metric</th>
                  <th className="text-left">Random Forest</th>
                  <th className="text-left">XGBoost</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Accuracy</td>
                  <td>{(metrics.random_forest.accuracy * 100).toFixed(2)}%</td>
                  <td>{(metrics.xgboost.accuracy * 100).toFixed(2)}%</td>
                </tr>
                <tr>
                  <td>F1 Score</td>
                  <td>{(metrics.random_forest.f1_score * 100).toFixed(2)}%</td>
                  <td>{(metrics.xgboost.f1_score * 100).toFixed(2)}%</td>
                </tr>
              </tbody>
            </table>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <h4 className="text-sm font-medium mb-1">Random Forest Features</h4>
                <img
                  src="/ml_model/feature_importance.png"
                  alt="RF Importance"
                  className="rounded border"
                />
              </div>
              <div>
                <h4 className="text-sm font-medium mb-1">XGBoost Features</h4>
                <img
                  src="/ml_model/xgb_feature_importance.png"
                  alt="XGB Importance"
                  className="rounded border"
                />
              </div>
            </div>

            <p className="text-sm text-gray-600 leading-relaxed">
              Both models take in encoded features like material, weight (log/binned), transport type,
              recyclability, and origin. They predict eco scores (A+ to F) based on patterns learned during training.
              The charts above show which features influenced decisions most.
            </p>
            <div className="mt-4 text-sm text-blue-600">
                <a href="/your-dissertation.pdf" target="_blank" rel="noopener noreferrer">
                    📄 View Full Dissertation (PDF)
                </a>
            </div>

          </>
        )}
      </div>
    </div>
  );
}

 
