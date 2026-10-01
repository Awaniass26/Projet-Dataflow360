/**
 * Page Alertes de fraude
 * - KPI
 * - Filtres par jour / mois / année
 * - Affiche 5 alertes puis scroll (voir plus)
 */

import { useMemo, useState } from "react";
import { Header } from "@/components/layout/Header";
import { Card, CardTitle, CardValue } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import { useFraudAlerts, useFraudStats } from "@/hooks/useFraud";
import { formatAmount } from "@/lib/utils";
import type { FraudSeverity, FraudStatus } from "@/types/fraud";
import { Search } from "lucide-react";

const PAGE_SIZE = 5;

type Period = "jour" | "mois" | "année" | "tout";

export function FraudAlertsPage() {
  const { data: alerts, isLoading: alertsLoading, error: alertsError } = useFraudAlerts();
  const { data: stats, isLoading: statsLoading } = useFraudStats();

  const [period, setPeriod] = useState<Period>("tout");
  const [severity, setSeverity] = useState<FraudSeverity | "all">("all");
  const [status, setStatus] = useState<FraudStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const filtered = useMemo(() => {
    if (!alerts) return [];
    const now = new Date("2026-09-30"); // date de référence démo

    return alerts.filter((a) => {
      const alertDate = new Date(a.date);

      // Filtre période
      let matchPeriod = true;
      if (period === "jour") {
        matchPeriod =
          alertDate.getFullYear() === now.getFullYear() &&
          alertDate.getMonth() === now.getMonth() &&
          alertDate.getDate() === now.getDate();
      } else if (period === "mois") {
        matchPeriod =
          alertDate.getFullYear() === now.getFullYear() &&
          alertDate.getMonth() === now.getMonth();
      } else if (period === "année") {
        matchPeriod = alertDate.getFullYear() === now.getFullYear();
      }

      const matchSeverity = severity === "all" || a.severity === severity;
      const matchStatus = status === "all" || a.status === status;
      const matchSearch =
        !search ||
        a.clientName.toLowerCase().includes(search.toLowerCase()) ||
        a.transactionId.toLowerCase().includes(search.toLowerCase()) ||
        a.reason.toLowerCase().includes(search.toLowerCase());

      return matchPeriod && matchSeverity && matchStatus && matchSearch;
    });
  }, [alerts, period, severity, status, search]);

  const visible = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  const resetVisible = () => setVisibleCount(PAGE_SIZE);

  if (alertsLoading || statsLoading) {
    return <Loading message="Chargement des alertes fraude..." />;
  }
  if (alertsError || !alerts) {
    return <ErrorMessage message="Impossible de charger les alertes." />;
  }

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
            <CardValue>{stats.totalAlerts}</CardValue>
          </Card>
          <Card>
            <CardTitle>Critiques</CardTitle>
            <CardValue className="text-danger">{stats.criticalAlerts}</CardValue>
          </Card>
          <Card>
            <CardTitle>Nouvelles</CardTitle>
            <CardValue className="text-warning">{stats.newAlerts}</CardValue>
          </Card>
          <Card>
            <CardTitle>Résolues aujourd'hui</CardTitle>
            <CardValue className="text-success">{stats.resolvedToday}</CardValue>
          </Card>
          <Card>
            <CardTitle>Score risque moyen</CardTitle>
            <CardValue>{stats.averageRiskScore}</CardValue>
          </Card>
        </div>
      )}

      {/* Filtres */}
      <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher client, transaction, raison..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); resetVisible(); }}
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>

        {/* Période : jour / mois / année */}
        <div className="flex rounded-lg border border-gray-300 p-0.5">
          {(["jour", "mois", "année", "tout"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => { setPeriod(p); resetVisible(); }}
              className={`rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors ${
                period === p
                  ? "bg-primary-600 text-white"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        <select
          value={severity}
          onChange={(e) => { setSeverity(e.target.value as FraudSeverity | "all"); resetVisible(); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
        >
          <option value="all">Toutes sévérités</option>
          <option value="basse">Basse</option>
          <option value="moyenne">Moyenne</option>
          <option value="haute">Haute</option>
          <option value="critique">Critique</option>
        </select>

        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value as FraudStatus | "all"); resetVisible(); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
        >
          <option value="all">Tous statuts</option>
          <option value="nouvelle">Nouvelle</option>
          <option value="en_cours">En cours</option>
          <option value="résolue">Résolue</option>
          <option value="fausse_alerte">Fausse alerte</option>
        </select>
      </div>

      <p className="mb-3 text-sm text-gray-500">
        {filtered.length} alerte{filtered.length > 1 ? "s" : ""} trouvée{filtered.length > 1 ? "s" : ""}
      </p>

      {/* Tableau */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Client</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Montant</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Sévérité</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Raison</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Statut</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {visible.map((alert) => (
                <tr key={alert.id} className="hover:bg-gray-50 transition-colors">
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="font-medium text-gray-900">{alert.clientName}</div>
                    <div className="text-xs text-gray-500">{alert.transactionId}</div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 font-medium text-gray-900">
                    {formatAmount(alert.amount)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge variant="severity" value={alert.severity}>{alert.severity}</Badge>
                  </td>
                  <td className="max-w-xs px-6 py-4 text-sm text-gray-600">{alert.reason}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm capitalize text-gray-600">
                    {alert.status.replace("_", " ")}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {new Date(alert.date).toLocaleString("fr-FR", {
                      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
                    })}
                  </td>
                </tr>
              ))}
              {visible.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-sm text-gray-500">
                    Aucune alerte trouvée pour ces filtres
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {hasMore && (
          <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 text-center">
            <button
              onClick={() => setVisibleCount((v) => v + PAGE_SIZE)}
              className="text-sm font-medium text-primary-600 hover:text-primary-800"
            >
              Voir plus ({filtered.length - visibleCount} restant{filtered.length - visibleCount > 1 ? "s" : ""})
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
