/**
 * Page Dashboard — KPI + graphiques
 */

import { Header } from "@/components/layout/Header";
import { Card, CardTitle, CardValue } from "@/components/ui/Card";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import { useDashboardKPI, useScoreDistribution, useMonthlyTrend } from "@/hooks/useDashboard";
import { formatAmount } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from "recharts";

export function DashboardPage() {
  const { data: kpi, isLoading: kpiLoading, error: kpiError } = useDashboardKPI();
  const { data: distribution } = useScoreDistribution();
  const { data: trend } = useMonthlyTrend();

  if (kpiLoading) return <Loading message="Chargement du dashboard..." />;
  if (kpiError || !kpi) return <ErrorMessage message="Impossible de charger les KPI." />;

  return (
    <div>
      <Header
        title="Dashboard"
        subtitle="Vue d'ensemble du scoring crédit et de la détection de fraude"
      />

      {/* KPI Cards */}
      <div className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
        <Card>
          <CardTitle>Score moyen</CardTitle>
          <CardValue>{kpi.averageCreditScore.toFixed(3)}</CardValue>
        </Card>
        <Card>
          <CardTitle>Total clients</CardTitle>
          <CardValue>{kpi.totalClients.toLocaleString("fr-FR")}</CardValue>
        </Card>
        <Card>
          <CardTitle>Clients à risque</CardTitle>
          <CardValue className="text-danger">{kpi.highRiskClients}</CardValue>
        </Card>
        <Card>
          <CardTitle>Alertes/jour</CardTitle>
          <CardValue className="text-warning">{kpi.fraudAlertsToday}</CardValue>
        </Card>
        <Card>
          <CardTitle>Transactions</CardTitle>
          <CardValue>{kpi.totalTransactionsToday.toLocaleString("fr-FR")}</CardValue>
        </Card>
        <Card>
          <CardTitle>Volume/jour</CardTitle>
          <CardValue className="text-lg">{formatAmount(kpi.totalVolumeToday)}</CardValue>
        </Card>
        <Card>
          <CardTitle>Inscriptions/Semaine</CardTitle>
          <CardValue className="text-primary-600">{kpi.newRegistrationsThisWeek}</CardValue>
        </Card>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="mb-4 text-base font-semibold text-gray-900">
            Distribution des scores de crédit
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Clients" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h3 className="mb-4 text-base font-semibold text-gray-900">
            Évolution score, fraudes & inscriptions
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="averageScore" name="Score moyen" stroke="#3b82f6" strokeWidth={2} dot={{ r: 0.5 }} />
                <Line yAxisId="right" type="monotone" dataKey="fraudCount" name="Alertes fraude" stroke="#dc2626" strokeWidth={2} dot={{ r: 0.5 }} />
                <Line yAxisId="right" type="monotone" dataKey="registrations" name="Inscriptions" stroke="#16a34a" strokeWidth={2} dot={{ r: 0.5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
