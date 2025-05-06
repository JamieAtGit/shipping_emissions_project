// src/hooks/useAuth.js
import { useEffect, useState } from "react";

export default function useAuth() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    const checkSession = async () => {
      try {
        const res = await fetch("http://localhost:5000/me", {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
          localStorage.setItem("user", JSON.stringify(data));
        } else {
          setUser(null);
          localStorage.removeItem("user");
        }
      } catch {
        setUser(null);
      }
    };
    checkSession();
  }, []);

  const logout = async () => {
    await fetch("http://localhost:5000/logout", {
      method: "POST",
      credentials: "include"
    });
    setUser(null);
    localStorage.removeItem("user");
  };

  return { user, setUser, logout };
}
