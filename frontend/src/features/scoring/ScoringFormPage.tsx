/**
 * Page Formulaire d'inscription au scoring crédit
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { submitScoringForm } from "@/services/clients";
import type { ScoringFormData } from "@/types/client";

const initialForm: ScoringFormData = {
  firstName: "",
  lastName: "",
  phone: "",
  email: "",
  city: "",
  accountAgeMonths: 12,
  averageMonthlyDeposit: 0,
  averageMonthlyWithdrawal: 0,
  totalTransactionsLast3Months: 0,
  hasLoanHistory: false,
  occupation: "",
};

export function ScoringFormPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<ScoringFormData>(initialForm);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ score: number; clientId: number } | null>(null);
  const [error, setError] = useState("");

  const update = (field: keyof ScoringFormData, value: string | number | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);

    try {
      if (!form.firstName || !form.lastName || !form.phone || !form.city) {
        throw new Error("Veuillez remplir tous les champs obligatoires.");
      }
      const res = await submitScoringForm(form);
      setResult({ score: res.score, clientId: res.clientId });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div>
        <Header title="Résultat du scoring" subtitle="Inscription enregistrée avec succès" />
        <Card className="mx-auto max-w-lg text-center">
          <p className="text-sm text-gray-500">Score de crédit calculé</p>
          <p className="mt-2 text-5xl font-bold text-primary-600">{result.score}</p>
          <p className="mt-2 text-sm text-gray-400">sur 1000</p>
          <p className="mt-6 text-sm text-gray-600">
            Le client <strong>{form.firstName} {form.lastName}</strong> a été ajouté à l'historique.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={() => navigate(`/clients`)}
              className="rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-700"
            >
              Voir l'historique clients
            </button>
            <button
              onClick={() => {
                setResult(null);
                setForm(initialForm);
              }}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Nouveau formulaire
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Header
        title="Formulaire de scoring crédit"
        subtitle="Inscription d'un nouveau client pour évaluation du risque de crédit"
      />

      <Card className="max-w-3xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Identité */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
              Identité
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Prénom *</label>
                <input
                  type="text"
                  required
                  value={form.firstName}
                  onChange={(e) => update("firstName", e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Nom *</label>
                <input
                  type="text"
                  required
                  value={form.lastName}
                  onChange={(e) => update("lastName", e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Téléphone *</label>
                <input
                  type="tel"
                  required
                  placeholder="+221 77 000 00 00"
                  value={form.phone}
                  onChange={(e) => update("phone", e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => update("email", e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Ville *</label>
                <input
                  type="text"
                  required
                  value={form.city}
                  onChange={(e) => update("city", e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Profession</label>
                <input
                  type="text"
                  value={form.occupation}
                  onChange={(e) => update("occupation", e.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Données Mobile Money */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
              Données Mobile Money
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Ancienneté du compte (mois)
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.accountAgeMonths}
                  onChange={(e) => update("accountAgeMonths", Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Transactions (3 derniers mois)
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.totalTransactionsLast3Months}
                  onChange={(e) => update("totalTransactionsLast3Months", Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Dépôt mensuel moyen (FCFA)
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.averageMonthlyDeposit}
                  onChange={(e) => update("averageMonthlyDeposit", Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Retrait mensuel moyen (FCFA)
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.averageMonthlyWithdrawal}
                  onChange={(e) => update("averageMonthlyWithdrawal", Number(e.target.value))}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <input
                    type="checkbox"
                    checked={form.hasLoanHistory}
                    onChange={(e) => update("hasLoanHistory", e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  A déjà contracté un crédit / prêt
                </label>
              </div>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <div className="flex justify-end gap-3 border-t border-gray-100 pt-6">
            <button
              type="button"
              onClick={() => setForm(initialForm)}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Réinitialiser
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? "Calcul du score..." : "Calculer le score"}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
