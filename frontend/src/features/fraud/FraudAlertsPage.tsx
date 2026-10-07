/**
 * Page Alertes de fraude
 * - KPI issus de GET /fraud/stats
 * - Liste paginée et filtrée côté serveur (GET /fraud/alerts)
 * - Changement de statut d'une alerte (PATCH /fraud/alerts/{id})
 */

import { useState } from "react";
import axios from "axios";
import { Header } from "@/components/layout/Header";
import { Card, CardTitle, CardValue } from "@/components/ui/Card";
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
import type { FraudStatus, RiskLevel } from "@/types/fraud";

const PAGE_SIZE = 10;

// Nom enregistré dans "reviewed_by" tant qu'il n'y a pas d'authentification réelle
import { getStoredUser } from "@/services/auth";

const REVIEWER = getStoredUser()?.email ?? "analyste";

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const apiMessage = err.response?.data?.error?.message;
    if (typeof apiMessage === "string") return apiMessage;
    if (err.code === "ERR_NETWORK") return "Impossible de joindre l'API.";
  }
  return err instanceof Error ? err.message : "Une erreur est survenue.";
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

  if (alertsLoading || statsLoading) {
    return <Loading message="Chargement des alertes fraude..." />;
  }
  if (alertsError || !alerts) {
    return <ErrorMessage message={getErrorMessage(alertsError) || "Impossible de charger les alertes."} />;
  }

  const pending = stats?.alerts_by_status.pending ?? 0;

  return (
    <div>
      <Header
        title="Alertes Fraude"
        subtitle="Détection et suivi des comportements à risque"
      />

      {/* KPI */}
      {stats && (
        <div className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardTitle>Total alertes</CardTitle>
            <CardValue>{stats.total_alerts}</CardValue>
          </Card>
          <Card>
            <CardTitle>Risque élevé</CardTitle>
            <CardValue className="text-danger">
              {stats.alerts_by_risk_level.high ?? 0}
            </CardValue>
          </Card>
          <Card>
            <CardTitle>En attente</CardTitle>
            <CardValue className="text-warning">{pending}</CardValue>
          </Card>
          <Card>
            <CardTitle>Traitées</CardTitle>
            <CardValue className="text-success">
              {stats.total_alerts - pending}
            </CardValue>
          </Card>
          <Card>
            <CardTitle>Taux de transactions suspectes</CardTitle>
            <CardValue>{(stats.suspicious_rate * 100).toFixed(3)} %</CardValue>
          </Card>
        </div>
      )}

      {/* Filtres (appliqués côté serveur) */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <select
          value={riskLevel}
          onChange={(e) => {
            setRiskLevel(e.target.value as RiskLevel | "all");
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
        >
          <option value="all">Tous niveaux de risque</option>
          {RISK_LEVELS.map((level) => (
            <option key={level} value={level}>
              Risque {RISK_LABELS[level].toLowerCase()}
            </option>
          ))}
        </select>

        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as FraudStatus | "all");
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
        >
          <option value="all">Tous statuts</option>
          {FRAUD_STATUSES.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>

        <p className="text-sm text-gray-500 sm:ml-auto">
          {alerts.total} alerte{alerts.total > 1 ? "s" : ""} trouvée
          {alerts.total > 1 ? "s" : ""}
        </p>
      </div>

      {updateAlert.isError && (
        <div className="mb-4">
          <ErrorMessage message={`Mise à jour impossible : ${getErrorMessage(updateAlert.error)}`} />
        </div>
      )}

      {/* Tableau */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Transaction</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Risque</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Explication</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Statut</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Traité par</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {alerts.items.map((alert) => (
                <tr key={alert.alert_id} className="transition-colors hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 font-medium text-gray-900">
                    {alert.transaction_id}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                    {alert.risk_score.toFixed(2)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge variant="risk" value={alert.risk_level}>
                      {RISK_LABELS[alert.risk_level]}
                    </Badge>
                  </td>
                  <td className="max-w-xs px-6 py-4 text-sm text-gray-600">
                    {alert.explanation ?? "—"}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Badge variant="status" value={alert.status}>
                        {STATUS_LABELS[alert.status]}
                      </Badge>
                      <select
                        aria-label={`Changer le statut de l'alerte ${alert.alert_id}`}
                        value={alert.status}
                        disabled={updateAlert.isPending}
                        onChange={(e) =>
                          updateAlert.mutate({
                            alertId: alert.alert_id,
                            payload: {
                              status: e.target.value as FraudStatus,
                              reviewed_by: REVIEWER,
                            },
                          })
                        }
                        className="rounded-md border border-gray-300 px-2 py-1 text-xs focus:border-primary-500 focus:outline-none disabled:opacity-50"
                      >
                        {FRAUD_STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {STATUS_LABELS[s]}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {alert.reviewed_by ?? "—"}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {new Date(alert.created_at).toLocaleString("fr-FR", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                </tr>
              ))}
              {alerts.items.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-sm text-gray-500">
                    Aucune alerte trouvée pour ces filtres
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-6 py-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="text-sm font-medium text-primary-600 hover:text-primary-800 disabled:cursor-not-allowed disabled:text-gray-400"
          >
            ← Précédent
          </button>
          <span className="text-sm text-gray-600">
            Page {alerts.page} / {Math.max(alerts.total_pages, 1)}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= alerts.total_pages}
            className="text-sm font-medium text-primary-600 hover:text-primary-800 disabled:cursor-not-allowed disabled:text-gray-400"
          >
            Suivant →
          </button>
        </div>
      </div>
    </div>
  );
}