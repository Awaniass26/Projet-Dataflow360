import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import axios from "axios";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useClients } from "@/hooks/useClients";
import { submitCreditScore } from "@/services/clients";
import { RISK_LABELS } from "@/lib/labels";
import type { CreditScoreFormInput, CreditScoreResponse } from "@/types/client";

const ACTIVITY_TYPES = [
  { value: "commerce", label: "Commerce" },
  { value: "agriculture", label: "Agriculture" },
  { value: "services", label: "Services" },
  { value: "salarie", label: "Salarié" },
  { value: "artisanat", label: "Artisanat" },
  { value: "autre", label: "Autre" },
] as const;

const DURATION_OPTIONS = [3, 6, 9, 12, 18, 24] as const;

interface FormState {
  accountId: string;
  age: string;
  requestedAmount: string;
  durationMonths: string;
  typeActivite: string;
}

const initialForm: FormState = {
  accountId: "",
  age: "",
  requestedAmount: "",
  durationMonths: "6",
  typeActivite: "commerce",
};

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(" · ");
    }
    const apiMessage = err.response?.data?.error?.message;
    if (typeof apiMessage === "string") return apiMessage;
    if (err.code === "ERR_NETWORK") return "Impossible de joindre l'API.";
  }
  return err instanceof Error ? err.message : "Une erreur est survenue.";
}

function riskBadgeVariant(
  level: CreditScoreResponse["risk_level"]
): "success" | "warning" | "danger" | "default" {
  if (level === "low") return "success";
  if (level === "medium") return "warning";
  if (level === "high") return "danger";
  return "default";
}

export function ScoringFormPage() {
  const { data: clients, isLoading: clientsLoading } = useClients(100);
  const [form, setForm] = useState<FormState>(initialForm);
  const [validationError, setValidationError] = useState("");
  const [result, setResult] = useState<CreditScoreResponse | null>(null);

  const mutation = useMutation({
    mutationFn: submitCreditScore,
    onSuccess: (data) => setResult(data),
  });

  const update = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  /** Préremplit l'âge depuis la fiche client (modifiable). */
  const onSelectClient = (clientId: string) => {
    const client = clients?.find((c) => c.client_id === clientId);
    setForm((prev) => ({
      ...prev,
      accountId: clientId,
      age: client ? String(client.age) : prev.age,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError("");
    setResult(null);

    const age = Number(form.age);
    const requestedAmount = Number(form.requestedAmount);
    const durationMonths = Number(form.durationMonths);

    if (!form.accountId.trim()) {
      return setValidationError("Sélectionnez un client.");
    }
    if (!Number.isInteger(age) || age < 18 || age > 120) {
      return setValidationError("L'âge doit être un entier entre 18 et 120 ans.");
    }
    if (!(requestedAmount > 0)) {
      return setValidationError("Le montant demandé doit être supérieur à 0.");
    }
    if (!Number.isInteger(durationMonths) || durationMonths <= 0) {
      return setValidationError("La durée doit être un nombre de mois valide.");
    }
    if (!form.typeActivite.trim()) {
      return setValidationError("Indiquez le type d'activité.");
    }

    const payload: CreditScoreFormInput = {
      account_id: form.accountId.trim(),
      age,
      montant_credit_demande: requestedAmount,
      duree_credit_demande: durationMonths,
      type_activite: form.typeActivite.trim().toLowerCase(),
    };

    mutation.mutate(payload);
  };

  const selectedClient = clients?.find((c) => c.client_id === form.accountId);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scoring crédit"
        subtitle="Saisissez les données métier (client, âge, montant, durée, activité). Les features comportementales sont calculées par le backend."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label-field">Client</label>
              {clientsLoading ? (
                <p className="text-sm text-slate-500">Chargement des clients…</p>
              ) : (
                <select
                  value={form.accountId}
                  onChange={(e) => onSelectClient(e.target.value)}
                  className="input-field"
                >
                  <option value="">— Sélectionner un client —</option>
                  {(clients ?? []).map((c) => (
                    <option key={c.client_id} value={c.client_id}>
                      {c.name} ({c.client_id}) — {c.region}
                    </option>
                  ))}
                </select>
              )}
              {selectedClient && (
                <p className="mt-1.5 text-xs text-slate-500">
                  {selectedClient.sexe} · {selectedClient.account_type} ·{" "}
                  {selectedClient.region}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="label-field">Âge (ans)</label>
                <input
                  type="number"
                  min={18}
                  max={120}
                  value={form.age}
                  onChange={(e) => update("age", e.target.value)}
                  className="input-field"
                  placeholder="ex. 32"
                />
              </div>
              <div>
                <label className="label-field">Type d&apos;activité</label>
                <select
                  value={form.typeActivite}
                  onChange={(e) => update("typeActivite", e.target.value)}
                  className="input-field"
                >
                  {ACTIVITY_TYPES.map((a) => (
                    <option key={a.value} value={a.value}>
                      {a.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="label-field">Montant demandé (XOF)</label>
                <input
                  type="number"
                  min={1}
                  step={1000}
                  value={form.requestedAmount}
                  onChange={(e) => update("requestedAmount", e.target.value)}
                  className="input-field"
                  placeholder="ex. 150000"
                />
              </div>
              <div>
                <label className="label-field">Durée (mois)</label>
                <select
                  value={form.durationMonths}
                  onChange={(e) => update("durationMonths", e.target.value)}
                  className="input-field"
                >
                  {DURATION_OPTIONS.map((m) => (
                    <option key={m} value={m}>
                      {m} mois
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 text-xs text-slate-600">
              <p className="font-medium text-slate-700">
                Calculé automatiquement par l&apos;API (pas saisi ici)
              </p>
              <ul className="mt-1 list-inside list-disc space-y-0.5">
                <li>Ancienneté du compte</li>
                <li>Nb transactions / entrées / sorties / solde moyen (90 j)</li>
                <li>Régularité des revenus, stabilité des flux</li>
                <li>Historique de crédits (précédents, retards, impayés)</li>
              </ul>
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

        <Card className="lg:col-span-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Résultat
          </h2>

          {!result && !mutation.isPending && (
            <p className="mt-4 text-sm text-slate-400">
              Le score s&apos;affichera ici après soumission.
            </p>
          )}

          {mutation.isPending && (
            <p className="mt-4 text-sm text-slate-500">Analyse en cours…</p>
          )}

          {result && (
            <div className="mt-4 space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                {result.risk_level && (
                  <Badge variant={riskBadgeVariant(result.risk_level)}>
                    {RISK_LABELS[result.risk_level] ?? result.risk_level}
                  </Badge>
                )}
                {result.is_simulation && (
                  <Badge variant="warning">Simulation</Badge>
                )}
                {result.eligible === true && (
                  <Badge variant="success">Éligible</Badge>
                )}
                {result.eligible === false && (
                  <Badge variant="danger">Non éligible</Badge>
                )}
              </div>

              <div>
                <p className="text-xs text-slate-500">Score de risque</p>
                <p className="text-3xl font-bold text-slate-900">
                  {result.risk_score != null
                    ? `${(result.risk_score * 100).toFixed(1)} %`
                    : "—"}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500">N° demande</p>
                <p className="font-mono text-sm text-slate-800">
                  {result.application_id}
                </p>
              </div>

              <p className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">
                {result.message}
              </p>

              <p className="text-xs text-slate-400">
                Aide à la décision uniquement — l&apos;octroi reste une décision
                métier humaine.
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}