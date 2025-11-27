import { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "./components/Navbar";
import LoginForm from "./components/LoginForm";
import SignUpForm from "./components/SignUpForm";

export default function Layout() {
  const [dark, setDark] = useState(() => localStorage.getItem("theme") === "dark");
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg)] text-[var(--text)] transition-colors duration-300">
      <Navbar
        dark={dark}
        setDark={setDark}
        onShowLogin={() => setShowLogin(true)}
        onShowSignup={() => setShowSignup(true)}
      />

      <main className="flex-grow flex flex-col items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
        <div className="w-full max-w-5xl">
          <Outlet />
        </div>
      </main>

      <footer className="text-center py-6 text-sm text-[var(--text-muted)]">
        © 2025 PortoFino
      </footer>

      {showLogin && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <LoginForm onClose={() => setShowLogin(false)} />
        </div>
      )}
      {showSignup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <SignUpForm onClose={() => setShowSignup(false)} />
        </div>
      )}
    </div>
  );
}
