/**
 * Service Fraude
 */

import type { FraudAlert, FraudStats } from "@/types/fraud";
import { mockFraudAlerts, mockFraudStats } from "@/mocks/fraud";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getFraudAlerts(): Promise<FraudAlert[]> {
  await delay(350);
  return mockFraudAlerts;
}

export async function getFraudStats(): Promise<FraudStats> {
  await delay(250);
  return mockFraudStats;
}
