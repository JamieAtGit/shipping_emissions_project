// src/pages/LogOnPage.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";

export default function LogOnPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const res = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Invalid username or password");
        return;
      }

      // Protect against missing data.user
      const role = data.user?.role;

      if (role === "admin") {
        navigate("/admin");
      } else {
        navigate("/");
      }
    } catch (err) {
      console.error("Login failed", err);
      setError("Server error. Please try again.");
    }
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-16 p-6 border rounded shadow">
        <h2 className="text-2xl font-bold mb-4">🔐 Log In</h2>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            className="w-full border px-3 py-2"
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="w-full border px-3 py-2"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <p className="text-red-500 text-sm">❌ {error}</p>}
          <button className="bg-green-600 text-white px-4 py-2 rounded w-full hover:bg-green-700">
            Log In
          </button>
        </form>
        <p className="text-sm mt-4 text-gray-600">
          No account?{" "}
          <a href="/signup" className="text-blue-500 hover:underline">
            Sign up
          </a>
        </p>
      </div>
    </Layout>
  );
}
