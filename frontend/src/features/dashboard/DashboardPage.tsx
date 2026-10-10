import { PageHeader } from "@/components/ui/PageHeader";
import { Card, KpiCard } from "@/components/ui/Card";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import {
  useDashboardKPI,
  useScoreDistribution,
  useMonthlyTrend,
} from "@/hooks/useDashboard";
import { useFraudStats } from "@/hooks/useFraud";
import { formatAmount, formatNumber, formatPercent } from "@/lib/utils";
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
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ComposedChart,
} from "recharts";
import {
  Activity,
  ShieldAlert,
  TrendingUp,
  Users,
  MapPin,
  AlertTriangle,
} from "lucide-react";

const RISK_COLORS = {
  Faible: "#1B7A4A",
  Moyen: "#C4A035",
  Élevé: "#d33636",
};

const ZONE_COLORS = [
  "#1B4F9C",
  "#C4A035",
  "#1B7A4A",
  "#d33636",
  "#2B6BC4",
  "#D4B84A",
  "#22A05A",
  "#7c3aed",
  "#0891b2",
  "#ea580c",
];

export function DashboardPage() {
  const { data: kpi, isLoading: kpiLoading, error: kpiError } = useDashboardKPI();
  const { data: distribution } = useScoreDistribution();
  const { data: trend } = useMonthlyTrend();
  const { data: fraudStats } = useFraudStats();

  if (kpiLoading) return <Loading message="Chargement du dashboard décisionnel..." />;
  if (kpiError || !kpi) {
    return (
      <ErrorMessage message="Impossible de charger les KPI. Vérifiez que l'API est démarrée." />
    );
  }

  const statusPieData = fraudStats?.alerts_by_status
    ? Object.entries(fraudStats.alerts_by_status).map(([name, value]) => ({
        name:
          name === "pending"
            ? "En attente"
            : name === "confirmed"
              ? "Confirmées"
              : name === "dismissed"
                ? "Rejetées"
                : name === "reviewed"
                  ? "Revue"
                  : name,
        value: value as number,
      }))
    : [];

  const zoneData = (fraudStats?.alerts_by_zone ?? []).map((z) => ({
    zone: z.zone,
    alert_count: z.alert_count,
    transaction_count: z.transaction_count,
    alert_rate_pct: Math.round((z.alert_rate ?? 0) * 1000) / 10,
    alert_rate: z.alert_rate ?? 0,
  }));

  const totalAlerts = fraudStats?.total_alerts ?? 0;
  const suspiciousRate = fraudStats?.suspicious_rate ?? 0;
  const pending = fraudStats?.alerts_by_status?.pending ?? 0;

  return (
    <div className="animate-fade-in space-y-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <PageHeader
          title="Tableau de bord décisionnel"
          subtitle="Vue temps réel — Mobile Money Sénégal · Aide à la décision"
        />
        <div className="flex items-center gap-2 rounded-full bg-brand-green-soft px-3 py-1.5 text-xs font-semibold text-brand-green">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-green opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-green" />
          </span>
          Flux live · rafraîchissement auto
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <KpiCard
          title="Score crédit moyen"
          value={(kpi.averageCreditScore ?? 0).toFixed(3)}
          hint="Probabilité de défaut estimée"
          accent="blue"
        />
        <KpiCard
          title="Clients actifs"
          value={formatNumber(kpi.totalClients ?? 0)}
          accent="blue"
        />
        <KpiCard
          title="Clients à risque élevé"
          value={formatNumber(kpi.highRiskClients ?? 0)}
          hint="Score crédit HIGH"
          accent="danger"
        />
        <KpiCard
          title="Alertes fraude (jour)"
          value={formatNumber(kpi.fraudAlertsToday ?? 0)}
          accent="gold"
        />
        <KpiCard
          title="Transactions scorées"
          value={formatNumber(kpi.totalTransactionsToday ?? 0)}
          hint="Passées par le modèle"
          accent="green"
        />
        <KpiCard
          title="Volume suspect"
          value={formatAmount(kpi.totalVolumeToday ?? 0)}
          accent="gold"
        />
        <KpiCard
          title="Taux de suspicion"
          value={formatPercent(suspiciousRate)}
          hint="Alertes / transactions"
          accent="danger"
        />
        <KpiCard
          title="Alertes en attente"
          value={formatNumber(pending)}
          hint="À traiter par un analyste"
          accent="gold"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="flex items-start gap-3 rounded-2xl border border-brand-blue/20 bg-brand-blue-soft/50 p-4">
          <div className="rounded-xl bg-brand-blue/10 p-2">
            <ShieldAlert className="h-5 w-5 text-brand-blue" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">Priorité fraude</p>
            <p className="mt-0.5 text-xs text-slate-600">
              {pending > 0
                ? `${pending} alerte(s) HIGH en attente — traiter avant toute validation manuelle.`
                : "Aucune alerte en attente. Surveillance active."}
            </p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-brand-gold/20 bg-brand-gold-soft/50 p-4">
          <div className="rounded-xl bg-brand-gold/10 p-2">
            <TrendingUp className="h-5 w-5 text-brand-gold" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">Risque crédit</p>
            <p className="mt-0.5 text-xs text-slate-600">
              Score moyen {(kpi.averageCreditScore ?? 0).toFixed(3)}. Les demandes HIGH
              nécessitent un second regard.
            </p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-brand-green/20 bg-brand-green-soft/50 p-4">
          <div className="rounded-xl bg-brand-green/10 p-2">
            <Activity className="h-5 w-5 text-brand-green" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">Pipeline temps réel</p>
            <p className="mt-0.5 text-xs text-slate-600">
              Producer → Kafka → Consumer → modèle fraude → PostgreSQL. Mise à jour
              automatique.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Distribution risques crédit (barres) */}
        <Card className="animate-slide-up">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">
              Distribution des risques crédit
            </h3>
            <Users className="h-4 w-4 text-slate-400" />
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 12,
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                  }}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]} name="Demandes">
                  {(distribution || []).map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        RISK_COLORS[entry.range as keyof typeof RISK_COLORS] ||
                        "#1B4F9C"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* NOUVEAU : Taux d'alertes par zone géographique */}
        <Card className="animate-slide-up">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">
              Taux d&apos;alertes par zone géographique
            </h3>
            <MapPin className="h-4 w-4 text-slate-400" />
          </div>
          <div className="h-80">
            {zoneData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={zoneData}
                  layout="vertical"
                  margin={{ left: 8, right: 16, top: 8, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    type="number"
                    tick={{ fontSize: 11 }}
                    unit="%"
                    domain={[0, "auto"]}
                  />
                  <YAxis
                    type="category"
                    dataKey="zone"
                    width={90}
                    tick={{ fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 12,
                      border: "1px solid #e2e8f0",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                    }}
                    formatter={(value: number, name: string) => {
                      if (name === "Taux d'alertes") return [`${value} %`, name];
                      return [value, name];
                    }}
                    labelFormatter={(label) => `Zone : ${label}`}
                  />
                  <Legend />
                  <Bar
                    dataKey="alert_rate_pct"
                    name="Taux d'alertes"
                    radius={[0, 6, 6, 0]}
                    barSize={18}
                  >
                    {zoneData.map((_, index) => (
                      <Cell
                        key={`zone-${index}`}
                        fill={ZONE_COLORS[index % ZONE_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-slate-400">
                <MapPin className="h-8 w-8 text-slate-300" />
                <p>Aucune donnée de zone pour le moment.</p>
                <p className="text-xs">
                  Les alertes scorées apparaîtront ici par région client.
                </p>
              </div>
            )}
          </div>
          {zoneData.length > 0 && (
            <p className="mt-2 text-center text-xs text-slate-400">
              Taux = alertes / transactions de la zone · trié du plus élevé au plus
              bas
            </p>
          )}
        </Card>

        <Card className="animate-slide-up">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">
              Évolution des alertes fraude
            </h3>
            <AlertTriangle className="h-4 w-4 text-slate-400" />
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend || []}>
                <defs>
                  <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#d33636" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#d33636" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 12,
                    border: "1px solid #e2e8f0",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="fraudCount"
                  name="Alertes"
                  stroke="#d33636"
                  fill="url(#colorFraud)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="animate-slide-up">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">
              Statut des alertes fraude
            </h3>
            <ShieldAlert className="h-4 w-4 text-slate-400" />
          </div>
          <div className="h-80">
            {statusPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusPieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {statusPieData.map((_, index) => (
                      <Cell
                        key={`status-${index}`}
                        fill={
                          ["#C4A035", "#d33636", "#1B7A4A", "#1B4F9C"][index % 4]
                        }
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-slate-400">
                Aucune alerte pour le moment — le pipeline génère des scores en
                continu.
              </div>
            )}
          </div>
          <p className="mt-2 text-center text-xs text-slate-400">
            Total alertes : {formatNumber(totalAlerts)}
          </p>
        </Card>
      </div>

      {/* Détail zones : volume d'alertes */}
      {zoneData.length > 0 && (
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">
              Volume d&apos;alertes par zone géographique
            </h3>
            <MapPin className="h-4 w-4 text-slate-400" />
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="zone" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 12,
                    border: "1px solid #e2e8f0",
                  }}
                />
                <Legend />
                <Bar
                  dataKey="alert_count"
                  name="Alertes"
                  fill="#d33636"
                  radius={[6, 6, 0, 0]}
                />
                <Bar
                  dataKey="transaction_count"
                  name="Transactions"
                  fill="#1B4F9C"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      <Card>
        <h3 className="mb-4 text-sm font-semibold text-slate-800">
          Tendance des alertes (détail journalier)
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
                stroke="#1B4F9C"
                strokeWidth={2}
                dot={{ r: 3, fill: "#C4A035" }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
