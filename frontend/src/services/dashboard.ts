import api from "./api";

import type {
  DashboardKPI,
  ScoreDistribution,
  MonthlyTrend,
} from "@/types/dashboard";

interface ClientApi {
  client_id: string;
  age: number;
  sexe: string;
  region: string;
  account_type: string;
}

interface CreditStatsApi {
  total_applications: number;
  average_score: number | null;
  average_requested_amount: number | null;
  risk_distribution: Record<string, number>;
}

interface FraudStatsApi {
  total_transactions: number;
  total_alerts: number;
  suspicious_rate: number;
  suspicious_amount: number;
  alerts_by_status: Record<string, number>;
  alerts_by_risk_level: Record<string, number>;
  alerts_evolution: {
    date: string;
    alert_count: number;
    suspicious_amount: number;
  }[];
}

/**
 * Récupère les données nécessaires au dashboard.
 *
 * Il n'existe pas actuellement d'endpoint /dashboard.
 * On compose donc le dashboard à partir des APIs existantes.
 */
async function getDashboardData() {
  const [
    clientsResponse,
    creditResponse,
    fraudResponse,
  ] = await Promise.all([
    api.get<ClientApi[]>("/clients", {
      params: { limit: 100 },
    }),

    api.get<CreditStatsApi>("/credit/stats"),

    api.get<FraudStatsApi>("/fraud/stats"),
  ]);

  return {
    clients: clientsResponse.data,
    credit: creditResponse.data,
    fraud: fraudResponse.data,
  };
}

/**
 * KPI principaux.
 */
export async function getDashboardKPI(): Promise<DashboardKPI> {
  const {
    clients,
    credit,
    fraud,
  } = await getDashboardData();

  const highRiskClients =
    credit.risk_distribution.high ?? 0;

  return {
    averageCreditScore:
      credit.average_score ?? 0,

    totalClients:
      clients.length,

    highRiskClients,

    fraudAlertsToday:
      fraud.alerts_evolution
        .filter((item) => {
          const today = new Date()
            .toISOString()
            .slice(0, 10);

          return item.date === today;
        })
        .reduce(
          (sum, item) => sum + item.alert_count,
          0
        ),

    totalTransactionsToday:
      fraud.total_transactions,

    totalVolumeToday:
      fraud.suspicious_amount,

    newRegistrationsThisWeek:
      clients.length,
  };
}

/**
 * Distribution des niveaux de risque crédit.
 */
export async function getScoreDistribution(): Promise<
  ScoreDistribution[]
> {
  const { credit } = await getDashboardData();

  return [
    {
      range: "Faible",
      count: credit.risk_distribution.low ?? 0,
    },
    {
      range: "Moyen",
      count: credit.risk_distribution.medium ?? 0,
    },
    {
      range: "Élevé",
      count: credit.risk_distribution.high ?? 0,
    },
  ];
}

/**
 * Évolution des alertes fraude.
 *
 * Le backend ne fournit actuellement pas l'historique
 * des scores crédit mensuel. On utilise donc uniquement
 * l'évolution réelle des alertes fraude.
 */
export async function getMonthlyTrend(): Promise<
  MonthlyTrend[]
> {
  const { fraud } = await getDashboardData();

  return fraud.alerts_evolution.map((item) => ({
    month: item.date,
    averageScore: 0,
    fraudCount: item.alert_count,
    registrations: 0,
  }));
}