import { useQuery } from "@tanstack/react-query";
import {
  getDashboardKPI,
  getScoreDistribution,
  getMonthlyTrend,
} from "@/services/dashboard";

const REFRESH_INTERVAL = 5000;

export function useDashboardKPI() {
  return useQuery({
    queryKey: ["dashboard", "kpi"],
    queryFn: getDashboardKPI,
    refetchInterval: REFRESH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

export function useScoreDistribution() {
  return useQuery({
    queryKey: ["dashboard", "score-distribution"],
    queryFn: getScoreDistribution,
    refetchInterval: REFRESH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

export function useMonthlyTrend() {
  return useQuery({
    queryKey: ["dashboard", "monthly-trend"],
    queryFn: getMonthlyTrend,
    refetchInterval: REFRESH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}