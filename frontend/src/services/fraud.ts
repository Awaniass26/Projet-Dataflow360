/**
 * Services fraude.
 *
 * Aucun mock ici.
 * Toutes les données viennent de FastAPI.
 */

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

/**
 * GET /fraud/alerts
 * Les filtres sont appliqués côté serveur (undefined = paramètre omis).
 */
export async function getFraudAlerts({
  page = 1,
  pageSize = 50,
  riskLevel,
  status,
}: FraudAlertsParams = {}): Promise<FraudAlertListResponse> {
  const { data } = await api.get<FraudAlertListResponse>(
    "/fraud/alerts",
    {
      params: {
        page,
        page_size: pageSize,
        risk_level: riskLevel,
        status,
      },
    }
  );

  return data;
}

/**
 * GET /fraud/stats
 */
export async function getFraudStats(): Promise<FraudStats> {
  const { data } = await api.get<FraudStats>(
    "/fraud/stats"
  );

  return data;
}

/**
 * PATCH /fraud/alerts/{alert_id}
 */
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