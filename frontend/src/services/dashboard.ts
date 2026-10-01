/**
 * Service Dashboard
 */

import type { DashboardKPI, ScoreDistribution, MonthlyTrend } from "@/types/dashboard";
import { mockDashboardKPI, mockScoreDistribution, mockMonthlyTrend } from "@/mocks/dashboard";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getDashboardKPI(): Promise<DashboardKPI> {
  await delay(300);
  return mockDashboardKPI;
}

export async function getScoreDistribution(): Promise<ScoreDistribution[]> {
  await delay(250);
  return mockScoreDistribution;
}

export async function getMonthlyTrend(): Promise<MonthlyTrend[]> {
  await delay(250);
  return mockMonthlyTrend;
}
