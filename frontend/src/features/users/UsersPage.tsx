import { useState } from "react";
import { Navigate } from "react-router-dom";
import axios from "axios";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { isAdmin, createUser } from "@/services/auth";
import type { UserRole } from "@/types/auth";
import { ROLE_LABELS } from "@/lib/labels";
import { UserPlus } from "lucide-react";

export function UsersPage() {
  if (!isAdmin()) {
    return <Navigate to="/" replace />;
  }

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("analyst");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!fullName.trim() || !email.trim() || password.length < 8) {
      setError("Nom, email et mot de passe (min. 8 caractères) sont requis.");
      return;
    }

    setLoading(true);
    try {
      const user = await createUser({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        role,
      });
      setSuccess(
        `Utilisateur créé : ${user.full_name} (${user.email}) — rôle ${ROLE_LABELS[user.role] ?? user.role}`
      );
      setFullName("");
      setEmail("");
      setPassword("");
      setRole("analyst");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 403) {
          setError("Accès réservé aux administrateurs.");
        } else if (err.response?.status === 409) {
          setError("Cet email est déjà utilisé.");
        } else if (err.code === "ERR_NETWORK") {
          setError("Impossible de joindre l'API.");
        } else {
          const detail = err.response?.data?.detail;
          setError(
            typeof detail === "string" ? detail : "Échec de la création."
          );
        }
      } else {
        setError("Une erreur inattendue est survenue.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Utilisateurs"
      />

      <Card className="mx-auto max-w-lg">
        <div className="mb-6 flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gold-soft">
            <UserPlus className="h-5 w-5 text-brand-gold" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              Nouvel utilisateur
            </h2>
            <p className="text-xs text-slate-500">
              Appelle POST /auth/users (admin only)
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label-field">Nom complet</label>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input-field"
              disabled={loading}
            />
          </div>
          <div>
            <label className="label-field">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              disabled={loading}
            />
          </div>
          <div>
            <label className="label-field">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              minLength={8}
              disabled={loading}
            />
          </div>
          <div>
            <label className="label-field">Rôle</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="input-field"
              disabled={loading}
            >
              <option value="analyst">Analyste</option>
              <option value="admin">Administrateur</option>
            </select>
          </div>

          {error && (
            <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}
          {success && (
            <p className="rounded-xl bg-brand-green-soft px-3 py-2 text-sm text-brand-green">
              {success}
            </p>
          )}

          <button type="submit" disabled={loading} className="btn-gold w-full">
            {loading ? "Création…" : "Créer l'utilisateur"}
          </button>
        </form>
      </Card>
    </div>
  );
}
