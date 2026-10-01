/**
 * Page de connexion Dataflow
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@dataflow.com");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (email && password) {
      localStorage.setItem("access_token", "mock-jwt-token");
      navigate("/");
    } else {
      setError("Veuillez renseigner vos identifiants.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary-600 text-white font-bold text-xl">
            DF
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Dataflow</h1>
          <p className="mt-1 text-sm text-gray-500">
            Scoring Crédit & Détection de Fraude
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm"
        >
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Mot de passe</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              className="w-full rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              Se connecter
            </button>
          </div>
          <p className="mt-6 text-center text-xs text-gray-400">
            Mode démonstration — n'importe quel identifiant fonctionne
          </p>
        </form>
      </div>
    </div>
  );
}
