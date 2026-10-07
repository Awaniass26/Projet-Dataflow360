export interface DashboardKPI {
  averageCreditScore: number;
  totalClients: number;
  highRiskClients: number;
  fraudAlertsToday: number;
  totalTransactionsToday: number;
  totalVolumeToday: number;
  newRegistrationsThisWeek: number;
}

export interface ScoreDistribution {
  range: string;
  count: number;
}

export interface MonthlyTrend {
  month: string;
  averageScore: number;
  fraudCount: number;
  registrations: number;
}
