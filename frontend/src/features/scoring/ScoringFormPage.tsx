import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { PageHeader } from "@/components/ui/PageHeader";
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
      return setValidationError("La durée doit être un entier de mois > 0.");
    }
    if (
      repaymentScore !== undefined &&
      (repaymentScore < 0 || repaymentScore > 1)
    ) {
      return setValidationError("L'historique de remboursement doit être entre 0 et 1.");
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
        <PageHeader
          title="Résultat du scoring"
          subtitle={`Demande ${result.application_id}`}
        />
        <Card className="mx-auto max-w-lg text-center">
          {result.is_simulation ? (
            <div className="rounded-xl border border-amber-200 bg-brand-gold-soft p-4 text-left text-sm text-amber-900">
              <p className="font-semibold">Mode simulation</p>
              <p className="mt-1">{result.message}</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-slate-500">Score de risque</p>
              <p className="mt-2 text-5xl font-bold text-brand-blue">
                {result.risk_score !== null ? result.risk_score.toFixed(2) : "—"}
              </p>
              <p className="mt-2 text-sm text-slate-400">sur 1</p>
              {result.risk_level && (
                <div className="mt-4">
                  <Badge
                    variant={
                      result.risk_level === "high"
                        ? "danger"
                        : result.risk_level === "medium"
                          ? "warning"
                          : "success"
                    }
                  >
                    Risque {RISK_LABELS[result.risk_level]}
                  </Badge>
                </div>
              )}
              <p className="mt-4 text-sm text-slate-500">{result.message}</p>
            </>
          )}
          <div className="mt-8 flex justify-center gap-3">
            <button type="button" onClick={reset} className="btn-primary">
              Nouvelle demande
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Scoring crédit"
        subtitle="Évaluez le risque d'une demande de micro-crédit Mobile Money"
      />

      <Card className="mx-auto max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="label-field">Compte client</label>
            {clients && clients.length > 0 ? (
              <select
                value={form.accountId}
                onChange={(e) => update("accountId", e.target.value)}
                className="input-field"
              >
                <option value="">Sélectionner un client</option>
                {clients.map((c) => (
                  <option key={c.client_id} value={c.client_id}>
                    {c.name || c.client_id} — {c.region}
                  </option>
                ))}
              </select>
            ) : (
              <input
                value={form.accountId}
                onChange={(e) => update("accountId", e.target.value)}
                className="input-field"
                placeholder="ID compte"
              />
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="label-field">Montant demandé (XOF)</label>
              <input
                type="number"
                min={1}
                value={form.requestedAmount}
                onChange={(e) => update("requestedAmount", e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="label-field">Durée (mois)</label>
              <input
                type="number"
                min={1}
                value={form.durationMonths}
                onChange={(e) => update("durationMonths", e.target.value)}
                className="input-field"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="label-field">Revenus mensuels estimés</label>
              <input
                type="number"
                min={0}
                value={form.income}
                onChange={(e) => update("income", e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="label-field">Dépenses mensuelles estimées</label>
              <input
                type="number"
                min={0}
                value={form.expenses}
                onChange={(e) => update("expenses", e.target.value)}
                className="input-field"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="label-field">Volume tx mensuel</label>
              <input
                type="number"
                min={0}
                value={form.txVolume}
                onChange={(e) => update("txVolume", e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="label-field">Fréquence tx</label>
              <input
                type="number"
                min={0}
                value={form.txFrequency}
                onChange={(e) => update("txFrequency", e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="label-field">Hist. remboursement (0–1)</label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.01}
                value={form.repaymentScore}
                onChange={(e) => update("repaymentScore", e.target.value)}
                className="input-field"
              />
            </div>
          </div>

          {(validationError || mutation.isError) && (
            <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
              {validationError || getErrorMessage(mutation.error)}
            </p>
          )}

          <button
            type="submit"
            disabled={mutation.isPending}
            className="btn-primary w-full sm:w-auto"
          >
            {mutation.isPending ? "Calcul en cours…" : "Lancer le scoring"}
          </button>
        </form>
      </Card>
    </div>
  );
}
