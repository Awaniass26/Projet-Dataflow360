import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { login } from "@/services/auth";
import { Shield } from "lucide-react";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@dataflow360.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError("Veuillez renseigner vos identifiants.");
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          setError("Email ou mot de passe incorrect.");
        } else if (err.code === "ERR_NETWORK") {
          setError("Impossible de joindre l'API. Vérifiez que le backend tourne.");
        } else {
          setError("Erreur de connexion. Réessayez.");
        }
      } else {
        setError("Une erreur inattendue est survenue.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-surface px-4">
      {/* Fond décoratif discret */}
      <div className="pointer-events-none absolute inset-0 opacity-40">
        <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-brand-blue/10 blur-3xl" />
        <div className="absolute -right-16 top-1/3 h-64 w-64 rounded-full bg-brand-green/10 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-48 w-48 rounded-full bg-brand-gold/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <img
            src="/logo-senterangasafe.jpeg"
            alt="SenTerangaSafe"
            className="mx-auto h-20 w-20 rounded-full object-cover shadow-card ring-4 ring-white"
          />
          <h1 className="mt-5 text-2xl font-bold tracking-tight">
            <span className="text-brand-blue">Sen</span>
            <span className="text-brand-gold">Teranga</span>
            <span className="text-brand-green">Safe</span>
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Plateforme de détection de fraudes & scoring de crédit Mobile Money
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-slate-100 bg-white p-8 shadow-card"
        >
          <div className="mb-6 flex items-center gap-2 text-slate-700">
            <Shield className="h-5 w-5 text-brand-blue" />
            <h2 className="text-base font-semibold">Connexion sécurisée</h2>
          </div>

          <div className="space-y-5">
            <div>
              <label className="label-field">Email</label>
              <input
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                className="input-field"
              />
            </div>
            <div>
              <label className="label-field">Mot de passe</label>
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="input-field"
              />
            </div>
            {error && (
              <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </p>
            )}
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "Connexion…" : "Se connecter"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
