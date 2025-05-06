import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";


export default function AdminPage() {
  const [submissions, setSubmissions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [updatedLabel, setUpdatedLabel] = useState("");

  useEffect(() => {
    fetch("http://localhost:5000/admin/submissions")
      .then((res) => res.json())
      .then((data) => setSubmissions(data))
      .catch((err) => console.error("Error loading submissions:", err));
  }, []);

  const handleEdit = (index) => {
    setSelected(index);
    setUpdatedLabel(submissions[index].true_label || "");
  };

  const handleSave = () => {
    const item = { ...submissions[selected], true_label: updatedLabel };
    fetch("http://localhost:5000/admin/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item),
    })
      .then(() => {
        const updated = [...submissions];
        updated[selected].true_label = updatedLabel;
        setSubmissions(updated);
        setSelected(null);
      })
      .catch((err) => console.error("Update failed:", err));
  };

  return (
    <Layout> 
        <div className="max-w-5xl mx-auto py-10 px-4">
        <h2 className="text-2xl font-bold mb-4">🛠️ Admin Panel: Review Predictions</h2>
        <table className="w-full table-auto text-sm border">
            <thead>
            <tr className="bg-gray-100">
                <th className="p-2 border">Title</th>
                <th className="p-2 border">Predicted</th>
                <th className="p-2 border">True Label</th>
                <th className="p-2 border">Actions</th>
            </tr>
            </thead>
            <tbody>
            {submissions.map((item, index) => (
                <tr key={index} className="border-t">
                <td className="p-2 border">{item.title}</td>
                <td className="p-2 border">{item.predicted_label}</td>
                <td className="p-2 border">{index === selected ? (
                    <input
                    type="text"
                    value={updatedLabel}
                    onChange={(e) => setUpdatedLabel(e.target.value)}
                    className="border px-2 py-1 rounded"
                    />
                ) : (
                    item.true_label || "—"
                )}</td>
                <td className="p-2 border">
                    {index === selected ? (
                    <button
                        onClick={handleSave}
                        className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700"
                    >
                        Save
                    </button>
                    ) : (
                    <button
                        onClick={() => handleEdit(index)}
                        className="text-blue-500 hover:underline"
                    >
                        Edit
                    </button>
                    )}
                </td>
                </tr>
            ))}
            </tbody>
        </table>
        </div>
    </Layout>
  );
}
