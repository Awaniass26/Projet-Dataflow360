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

const REFRESH_INTERVAL = 1000;

export function useFraudAlerts(params: FraudAlertsParams = {}) {
  return useQuery({
    queryKey: ["fraud", "alerts", params],
    queryFn: () => getFraudAlerts(params),
    placeholderData: keepPreviousData,
    refetchInterval: REFRESH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

export function useFraudStats() {
  return useQuery({
    queryKey: ["fraud", "stats"],
    queryFn: getFraudStats,
    refetchInterval: REFRESH_INTERVAL,
    refetchIntervalInBackground: true,
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

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["fraud"],
      });
    },
  });
}