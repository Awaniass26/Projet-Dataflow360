import { PageHeader } from "@/components/ui/PageHeader";
import { Card, KpiCard } from "@/components/ui/Card";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import {
  useDashboardKPI,
  useScoreDistribution,
  useMonthlyTrend,
} from "@/hooks/useDashboard";
import { formatAmount, formatNumber } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from "recharts";

export function DashboardPage() {
  const { data: kpi, isLoading: kpiLoading, error: kpiError } = useDashboardKPI();
  const { data: distribution } = useScoreDistribution();
  const { data: trend } = useMonthlyTrend();

  if (kpiLoading) return <Loading message="Chargement du dashboard..." />;
  if (kpiError || !kpi) {
    return <ErrorMessage message="Impossible de charger les KPI." />;
  }

  return (
    <div>
      <PageHeader
        title="Dashboard"
      />

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <KpiCard
          title="Score crédit moyen"
          value={(kpi.averageCreditScore ?? 0).toFixed(3)}
          accent="blue"
        />
        <KpiCard
          title="Total clients"
          value={formatNumber(kpi.totalClients ?? 0)}
          accent="blue"
        />
        <KpiCard
          title="Clients à risque"
          value={formatNumber(kpi.highRiskClients ?? 0)}
          accent="danger"
        />
        <KpiCard
          title="Alertes du jour"
          value={formatNumber(kpi.fraudAlertsToday ?? 0)}
          accent="gold"
        />
        <KpiCard
          title="Transactions"
          value={formatNumber(kpi.totalTransactionsToday ?? 0)}
          accent="green"
        />
        <KpiCard
          title="Volume suspect"
          value={formatAmount(kpi.totalVolumeToday ?? 0)}
          accent="gold"
        />
        <KpiCard
          title="Clients chargés"
          value={formatNumber(kpi.newRegistrationsThisWeek ?? 0)}
          accent="green"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="mb-4 text-sm font-semibold text-slate-800">
            Distribution des risques crédit
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar
                  dataKey="count"
                  fill="#d33636"
                  radius={[6, 6, 0, 0]}
                  name="Demandes"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h3 className="mb-4 text-sm font-semibold text-slate-800">
            Évolution des alertes fraude
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="fraudCount"
                  name="Alertes"
                  stroke="#d33636"
                  strokeWidth={2}
                  dot={{ r: 0.5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
