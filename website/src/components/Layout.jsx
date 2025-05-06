import React from "react";
import Header from "./Header";
import Footer from "./Footer";

export default function Layout({ children }) {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-grow max-w-5xl mx-auto px-4 py-10">
        {children}
      </main>
      <Footer />
    </div>
  );
}
