import api from "./api";
import type {
  FraudAlert,
  FraudAlertListResponse,
  FraudAlertUpdate,
  FraudStats,
  FraudStatus,
  RiskLevel,
} from "@/types/fraud";

export interface FraudAlertsParams {
  page?: number;
  pageSize?: number;
  riskLevel?: RiskLevel;
  status?: FraudStatus;
}

export async function getFraudAlerts({
  page = 1,
  pageSize = 50,
  riskLevel,
  status,
}: FraudAlertsParams = {}): Promise<FraudAlertListResponse> {
  const { data } = await api.get<FraudAlertListResponse>("/fraud/alerts", {
    params: {
      page,
      page_size: pageSize,
      risk_level: riskLevel,
      status,
    },
  });
  return data;
}

export async function getFraudStats(): Promise<FraudStats> {
  const { data } = await api.get<FraudStats>("/fraud/stats");
  return data;
}

export async function updateFraudAlert(
  alertId: number,
  payload: FraudAlertUpdate
): Promise<FraudAlert> {
  const { data } = await api.patch<FraudAlert>(
    `/fraud/alerts/${alertId}`,
    payload
  );
  return data;
}
