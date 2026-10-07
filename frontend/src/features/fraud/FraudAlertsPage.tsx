import { useState } from "react";
import axios from "axios";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, KpiCard } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import {
  useFraudAlerts,
  useFraudStats,
  useUpdateFraudAlert,
} from "@/hooks/useFraud";
import {
  FRAUD_STATUSES,
  RISK_LABELS,
  RISK_LEVELS,
  STATUS_LABELS,
} from "@/lib/labels";
import { formatAmount, formatPercent } from "@/lib/utils";
import { getStoredUser } from "@/services/auth";
import type { FraudStatus, RiskLevel } from "@/types/fraud";

const PAGE_SIZE = 10;

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const apiMessage = err.response?.data?.error?.message;
    if (typeof apiMessage === "string") return apiMessage;
    if (err.code === "ERR_NETWORK") return "Impossible de joindre l'API.";
  }
  return err instanceof Error ? err.message : "Une erreur est survenue.";
}

function riskVariant(level: RiskLevel) {
  if (level === "high") return "danger" as const;
  if (level === "medium") return "warning" as const;
  return "success" as const;
}

export function FraudAlertsPage() {
  const [page, setPage] = useState(1);
  const [riskLevel, setRiskLevel] = useState<RiskLevel | "all">("all");
  const [status, setStatus] = useState<FraudStatus | "all">("all");

  const {
    data: alerts,
    isLoading: alertsLoading,
    error: alertsError,
  } = useFraudAlerts({
    page,
    pageSize: PAGE_SIZE,
    riskLevel: riskLevel === "all" ? undefined : riskLevel,
    status: status === "all" ? undefined : status,
  });
  const { data: stats, isLoading: statsLoading } = useFraudStats();
  const updateAlert = useUpdateFraudAlert();

  const reviewer = getStoredUser()?.email ?? "analyste";

  if (alertsLoading || statsLoading) {
    return <Loading message="Chargement des alertes fraude..." />;
  }
  if (alertsError || !alerts) {
    return (
      <ErrorMessage
        message={getErrorMessage(alertsError) || "Impossible de charger les alertes."}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Alertes Fraude"
        subtitle="Détection et suivi des comportements à risque Mobile Money"
      />

      {stats && (
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <KpiCard title="Total alertes" value={stats.total_alerts ?? 0} />
          <KpiCard
            title="Transactions"
            value={stats.total_transactions ?? 0}
            accent="green"
          />
          <KpiCard
            title="Taux suspect"
            value={formatPercent(stats.suspicious_rate ?? 0)}
            accent="gold"
          />
          <KpiCard
            title="Montant suspect"
            value={formatAmount(stats.suspicious_amount ?? 0)}
            accent="gold"
          />
          <KpiCard
            title="En attente"
            value={stats.alerts_by_status?.pending ?? 0}
            accent="danger"
          />
        </div>
      )}

      <Card className="mb-6">
        <div className="flex flex-wrap gap-3">
          <select
            value={riskLevel}
            onChange={(e) => {
              setRiskLevel(e.target.value as RiskLevel | "all");
              setPage(1);
            }}
            className="input-field !mt-0 w-auto min-w-[160px]"
          >
            <option value="all">Tous les risques</option>
            {RISK_LEVELS.map((r) => (
              <option key={r} value={r}>
                {RISK_LABELS[r]}
              </option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as FraudStatus | "all");
              setPage(1);
            }}
            className="input-field !mt-0 w-auto min-w-[180px]"
          >
            <option value="all">Tous les statuts</option>
            {FRAUD_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>
      </Card>

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100">
            <thead className="bg-slate-50/80">
              <tr>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Alerte
                </th>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Transaction
                </th>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Score
                </th>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Risque
                </th>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Statut
                </th>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {alerts.items.map((alert) => (
                <tr key={alert.alert_id} className="hover:bg-slate-50/80">
                  <td className="whitespace-nowrap px-5 py-3 text-sm font-medium">
                    #{alert.alert_id}
                  </td>
                  <td className="whitespace-nowrap px-5 py-3 font-mono text-xs text-slate-500">
                    {alert.transaction_id}
                  </td>
                  <td className="whitespace-nowrap px-5 py-3 text-sm font-semibold">
                    {(alert.risk_score ?? 0).toFixed(3)}
                  </td>
                  <td className="whitespace-nowrap px-5 py-3">
                    <Badge variant={riskVariant(alert.risk_level)}>
                      {RISK_LABELS[alert.risk_level]}
                    </Badge>
                  </td>
                  <td className="whitespace-nowrap px-5 py-3">
                    <Badge>{STATUS_LABELS[alert.status]}</Badge>
                  </td>
                  <td className="whitespace-nowrap px-5 py-3">
                    {alert.status === "pending" ? (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="text-xs font-semibold text-brand-green hover:underline"
                          disabled={updateAlert.isPending}
                          onClick={() =>
                            updateAlert.mutate({
                              alertId: alert.alert_id,
                              payload: {
                                status: "confirmed",
                                reviewed_by: reviewer,
                              },
                            })
                          }
                        >
                          Confirmer
                        </button>
                        <button
                          type="button"
                          className="text-xs font-semibold text-slate-500 hover:underline"
                          disabled={updateAlert.isPending}
                          onClick={() =>
                            updateAlert.mutate({
                              alertId: alert.alert_id,
                              payload: {
                                status: "dismissed",
                                reviewed_by: reviewer,
                              },
                            })
                          }
                        >
                          Rejeter
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {alerts.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-sm text-slate-500">
                    Aucune alerte pour ces filtres.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {alerts.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3">
            <p className="text-xs text-slate-400">
              Page {alerts.page} / {alerts.total_pages} · {alerts.total} alerte(s)
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="btn-secondary !py-1.5 !text-xs"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Précédent
              </button>
              <button
                type="button"
                className="btn-secondary !py-1.5 !text-xs"
                disabled={page >= alerts.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Suivant
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
