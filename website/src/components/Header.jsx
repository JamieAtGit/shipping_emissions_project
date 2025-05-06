import React from "react";
import { Link } from "react-router-dom"; // ✅ This was missing


export default function Header() {
  return (
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
    </div>
  );
}
