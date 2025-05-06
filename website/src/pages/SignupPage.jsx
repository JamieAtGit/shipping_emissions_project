// src/pages/SignupPage.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";

export default function SignupPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch("https://eco-backend-m26q.onrender.com/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Signup failed");

      navigate("/login");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Layout>
        <div className="max-w-md mx-auto mt-16 p-6 border rounded shadow">
        <h2 className="text-2xl font-bold mb-4">🆕 Sign Up</h2>
        <form onSubmit={handleSignup} className="space-y-4">
            <input
            className="w-full border px-3 py-2"
            type="text"
            placeholder="Choose a username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            />
            <input
            className="w-full border px-3 py-2"
            type="password"
            placeholder="Choose a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            />
            {error && <p className="text-red-500 text-sm">❌ {error}</p>}
            <button className="bg-blue-600 text-white px-4 py-2 rounded w-full hover:bg-blue-700">
            Sign Up
            </button>
        </form>
            <p className="text-sm mt-4 text-gray-600">
                Already have an account? <a href="/login" className="text-blue-500 hover:underline">Log in</a>
            </p>
        </div>
    </Layout>    
  );
}
