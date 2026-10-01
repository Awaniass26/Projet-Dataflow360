/**
 * Hooks React Query pour la fraude
 */

import { useQuery } from "@tanstack/react-query";
import { getFraudAlerts, getFraudStats } from "@/services/fraud";

export function useFraudAlerts() {
  return useQuery({
    queryKey: ["fraud", "alerts"],
    queryFn: getFraudAlerts,
  });
}

export function useFraudStats() {
  return useQuery({
    queryKey: ["fraud", "stats"],
    queryFn: getFraudStats,
  });
}
