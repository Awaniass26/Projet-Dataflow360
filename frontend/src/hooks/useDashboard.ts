/**
 * Hooks React Query pour le Dashboard
 */

import { useQuery } from "@tanstack/react-query";
import {
  getDashboardKPI,
  getScoreDistribution,
  getMonthlyTrend,
} from "@/services/dashboard";

export function useDashboardKPI() {
  return useQuery({
    queryKey: ["dashboard", "kpi"],
    queryFn: getDashboardKPI,
  });
}

export function useScoreDistribution() {
  return useQuery({
    queryKey: ["dashboard", "score-distribution"],
    queryFn: getScoreDistribution,
  });
}

export function useMonthlyTrend() {
  return useQuery({
    queryKey: ["dashboard", "monthly-trend"],
    queryFn: getMonthlyTrend,
  });
}
