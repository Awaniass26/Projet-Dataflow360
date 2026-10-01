/**
 * Données mockées — Dashboard KPI
 */

import type { DashboardKPI, ScoreDistribution, MonthlyTrend } from "@/types/dashboard";

export const mockDashboardKPI: DashboardKPI = {
  averageCreditScore: 612,
  totalClients: 1847,
  highRiskClients: 213,
  fraudAlertsToday: 7,
  totalTransactionsToday: 3421,
  totalVolumeToday: 187509,
  newRegistrationsThisWeek: 28,
};

export const mockScoreDistribution: ScoreDistribution[] = [
  { range: "0-300", count: 89 },
  { range: "301-500", count: 312 },
  { range: "501-650", count: 687 },
  { range: "651-750", count: 521 },
  { range: "751-850", count: 198 },
  { range: "851-1000", count: 40 },
];

export const mockMonthlyTrend: MonthlyTrend[] = [
  { month: "Avr", averageScore: 578, fraudCount: 42, registrations: 18 },
  { month: "Mai", averageScore: 585, fraudCount: 38, registrations: 22 },
  { month: "Juin", averageScore: 592, fraudCount: 51, registrations: 15 },
  { month: "Juil", averageScore: 601, fraudCount: 45, registrations: 28 },
  { month: "Août", averageScore: 608, fraudCount: 39, registrations: 31 },
  { month: "Sept", averageScore: 612, fraudCount: 47, registrations: 24 },
];
