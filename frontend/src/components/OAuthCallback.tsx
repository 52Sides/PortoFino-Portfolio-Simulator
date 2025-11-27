import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const access_token = params.get("access_token");
    const refresh_token = params.get("refresh_token");

    if (access_token && refresh_token) {
      setTokens(access_token, refresh_token);
      navigate("/", { replace: true });
    } else {
      navigate("/login", { replace: true });
    }
  }, [navigate, setTokens]);

  return (
    <div className="flex flex-col items-center justify-center mt-10">
      <div className="animate-spin border-4 border-[var(--accent)] border-t-transparent rounded-full w-12 h-12"></div>
      <p className="mt-4 text-[var(--text)] text-center">Logging in with Google...</p>
    </div>
  );
}
