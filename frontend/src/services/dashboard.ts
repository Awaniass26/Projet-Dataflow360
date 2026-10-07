/**
 * Dashboard : agrège /clients, /credit/stats, /fraud/stats
 */

import api from "./api";

import type {
  DashboardKPI,
  ScoreDistribution,
  MonthlyTrend,
} from "@/types/dashboard";
import type { ClientListResponse } from "@/types/client";

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

async function getDashboardData() {
  const [clientsResponse, creditResponse, fraudResponse] =
    await Promise.all([
      api.get<ClientListResponse>("/clients", {
        params: { page: 1, page_size: 100 },
      }),
      api.get<CreditStatsApi>("/credit/stats"),
      api.get<FraudStatsApi>("/fraud/stats"),
    ]);

  const clientsPayload = clientsResponse.data;
  // Compat : si un jour l'API renvoie un tableau brut
  const clients = Array.isArray(clientsPayload)
    ? clientsPayload
    : (clientsPayload.items ?? []);
  const clientsTotal = Array.isArray(clientsPayload)
    ? clientsPayload.length
    : (clientsPayload.total ?? clients.length);

  return {
    clients,
    clientsTotal,
    credit: creditResponse.data,
    fraud: fraudResponse.data,
  };
}

export async function getDashboardKPI(): Promise<DashboardKPI> {
  const { clientsTotal, credit, fraud } = await getDashboardData();

  const today = new Date().toISOString().slice(0, 10);

  const fraudAlertsToday = (fraud.alerts_evolution ?? [])
    .filter((item) => String(item.date).slice(0, 10) === today)
    .reduce((sum, item) => sum + (item.alert_count ?? 0), 0);

  return {
    averageCreditScore: credit.average_score ?? 0,
    totalClients: clientsTotal,
    highRiskClients: credit.risk_distribution?.high ?? 0,
    fraudAlertsToday,
    totalTransactionsToday: fraud.total_transactions ?? 0,
    totalVolumeToday: fraud.suspicious_amount ?? 0,
    newRegistrationsThisWeek: clientsTotal,
  };
}

export async function getScoreDistribution(): Promise<ScoreDistribution[]> {
  const { credit } = await getDashboardData();
  const dist = credit.risk_distribution ?? {};

  return [
    { range: "Faible", count: dist.low ?? 0 },
    { range: "Moyen", count: dist.medium ?? 0 },
    { range: "Élevé", count: dist.high ?? 0 },
  ];
}

export async function getMonthlyTrend(): Promise<MonthlyTrend[]> {
  const { fraud } = await getDashboardData();

  return (fraud.alerts_evolution ?? []).map((item) => ({
    month: String(item.date),
    averageScore: 0,
    fraudCount: item.alert_count ?? 0,
    registrations: 0,
  }));
}