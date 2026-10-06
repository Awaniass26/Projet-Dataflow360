import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getFraudAlerts,
  getFraudStats,
  updateFraudAlert,
  type FraudAlertsParams,
} from "@/services/fraud";
import type { FraudAlertUpdate } from "@/types/fraud";

export function useFraudAlerts(params: FraudAlertsParams = {}) {
  return useQuery({
    queryKey: ["fraud", "alerts", params],
    queryFn: () => getFraudAlerts(params),
    // Garde la page précédente affichée pendant le changement de page/filtre
    placeholderData: keepPreviousData,
  });
}

export function useFraudStats() {
  return useQuery({
    queryKey: ["fraud", "stats"],
    queryFn: getFraudStats,
  });
}

export function useUpdateFraudAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      alertId,
      payload,
    }: {
      alertId: number;
      payload: FraudAlertUpdate;
    }) => updateFraudAlert(alertId, payload),
    // Rafraîchit la liste ET les KPI
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["fraud"] }),
  });
}