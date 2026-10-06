/**
 * Page Scoring crédit
 * Envoie une demande de crédit à POST /credit/score et affiche la réponse.
 *
 * NB : tant qu'aucun modèle de crédit n'est branché côté API, la réponse est
 * une SIMULATION (aucun score réel). La page l'indique clairement.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useClients } from "@/hooks/useClients";
import { submitCreditScore } from "@/services/clients";
import { RISK_LABELS } from "@/lib/labels";
import type { CreditApplicationInput } from "@/types/client";

interface FormState {
  accountId: string;
  requestedAmount: string;
  durationMonths: string;
  income: string;
  expenses: string;
  txVolume: string;
  txFrequency: string;
  repaymentScore: string;
}

const initialForm: FormState = {
  accountId: "",
  requestedAmount: "",
  durationMonths: "6",
  income: "",
  expenses: "",
  txVolume: "",
  txFrequency: "",
  repaymentScore: "",
};

const inputClass =
  "mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500";

/** Champ vide → undefined (l'API accepte l'absence des champs optionnels). */
function toOptionalNumber(value: string): number | undefined {
  return value.trim() === "" ? undefined : Number(value);
}

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const apiMessage = err.response?.data?.error?.message;
    if (typeof apiMessage === "string") return apiMessage;
    if (err.code === "ERR_NETWORK") return "Impossible de joindre l'API.";
  }
  return err instanceof Error ? err.message : "Une erreur est survenue.";
}

export function ScoringFormPage() {
  const navigate = useNavigate();
  const { data: clients } = useClients(100);
  const [form, setForm] = useState<FormState>(initialForm);
  const [validationError, setValidationError] = useState("");

  const mutation = useMutation({ mutationFn: submitCreditScore });

  const update = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError("");

    const requestedAmount = Number(form.requestedAmount);
    const durationMonths = Number(form.durationMonths);
    const repaymentScore = toOptionalNumber(form.repaymentScore);

    if (!form.accountId.trim()) {
      return setValidationError("Veuillez indiquer l'identifiant du compte client.");
    }
    if (!(requestedAmount > 0)) {
      return setValidationError("Le montant demandé doit être supérieur à 0.");
    }
    if (!Number.isInteger(durationMonths) || durationMonths <= 0) {
      return setValidationError("La durée doit être un nombre entier de mois supérieur à 0.");
    }
    if (repaymentScore !== undefined && (repaymentScore < 0 || repaymentScore > 1)) {
      return setValidationError("L'historique de remboursement doit être compris entre 0 et 1.");
    }

    const payload: CreditApplicationInput = {
      application_id: `WEB-${Date.now()}`,
      account_id: form.accountId.trim(),
      requested_amount: requestedAmount,
      requested_duration_months: durationMonths,
      estimated_monthly_income: toOptionalNumber(form.income),
      estimated_monthly_expenses: toOptionalNumber(form.expenses),
      monthly_transaction_volume: toOptionalNumber(form.txVolume),
      monthly_transaction_frequency: toOptionalNumber(form.txFrequency),
      repayment_history_score: repaymentScore,
    };

    mutation.mutate(payload);
  };

  const reset = () => {
    mutation.reset();
    setForm(initialForm);
    setValidationError("");
  };

  const result = mutation.data;

  if (result) {
    return (
      <div>
        <Header
          title="Résultat du scoring"
          subtitle={`Demande ${result.application_id}`}
        />
        <Card className="mx-auto max-w-lg text-center">
          {result.is_simulation ? (
            <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 text-left text-sm text-orange-800">
              <p className="font-semibold">Mode simulation</p>
              <p className="mt-1">{result.message}</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500">Score de risque</p>
              <p className="mt-2 text-5xl font-bold text-primary-600">
                {result.risk_score !== null ? result.risk_score.toFixed(2) : "—"}
              </p>
              <p className="mt-2 text-sm text-gray-400">sur 1</p>
              {result.risk_level && (
                <div className="mt-4">
                  <Badge variant="risk" value={result.risk_level}>
                    Risque {RISK_LABELS[result.risk_level].toLowerCase()}
                  </Badge>
                </div>
              )}
              <p className="mt-4 text-sm text-gray-600">{result.message}</p>
            </>
          )}

          {result.explanation_factors && result.explanation_factors.length > 0 && (
            <ul className="mt-6 list-inside list-disc text-left text-sm text-gray-600">
              {result.explanation_factors.map((factor) => (
                <li key={factor}>{factor}</li>
              ))}
            </ul>
          )}

          <p className="mt-6 text-xs text-gray-400">
            Aide à la décision uniquement : ce résultat ne constitue pas une décision d'octroi de crédit.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button
              onClick={() => navigate("/clients")}
              className="rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-700"
            >
              Voir les clients
            </button>
            <button
              onClick={reset}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Nouvelle demande
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Header
        title="Scoring crédit"
        subtitle="Évaluation du risque d'une demande de micro-crédit"
      />

      <Card className="max-w-3xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Demande */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
              Demande
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">
                  Compte client *
                </label>
                <input
                  type="text"
                  required
                  list="client-ids"
                  placeholder="ex. CLI-000001"
                  value={form.accountId}
                  onChange={(e) => update("accountId", e.target.value)}
                  className={inputClass}
                />
                <datalist id="client-ids">
                  {clients?.map((c) => (
                    <option key={c.client_id} value={c.client_id}>
                      {c.region} · {c.account_type}
                    </option>
                  ))}
                </datalist>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Montant demandé (FCFA) *
                </label>
                <input
                  type="number"
                  required
                  min={1}
                  value={form.requestedAmount}
                  onChange={(e) => update("requestedAmount", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Durée (mois) *
                </label>
                <input
                  type="number"
                  required
                  min={1}
                  step={1}
                  value={form.durationMonths}
                  onChange={(e) => update("durationMonths", e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>
          </div>

          {/* Données financières (facultatives) */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
              Données financières (facultatives)
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Revenu mensuel estimé (FCFA)
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.income}
                  onChange={(e) => update("income", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Dépenses mensuelles estimées (FCFA)
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.expenses}
                  onChange={(e) => update("expenses", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Volume mensuel de transactions (FCFA)
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.txVolume}
                  onChange={(e) => update("txVolume", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Transactions par mois
                </label>
                <input
                  type="number"
                  min={0}
                  step={1}
                  value={form.txFrequency}
                  onChange={(e) => update("txFrequency", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">
                  Historique de remboursement (0 = mauvais, 1 = excellent)
                </label>
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={form.repaymentScore}
                  onChange={(e) => update("repaymentScore", e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>
          </div>

          {(validationError || mutation.isError) && (
            <p className="text-sm text-red-600">
              {validationError || getErrorMessage(mutation.error)}
            </p>
          )}

          <div className="flex justify-end gap-3 border-t border-gray-100 pt-6">
            <button
              type="button"
              onClick={reset}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Réinitialiser
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {mutation.isPending ? "Calcul du score..." : "Calculer le score"}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}