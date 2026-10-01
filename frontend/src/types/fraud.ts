/**
 * Types liés à la détection de fraude
 */

export type FraudSeverity = "basse" | "moyenne" | "haute" | "critique";
export type FraudStatus = "nouvelle" | "en_cours" | "résolue" | "fausse_alerte";

export interface FraudAlert {
  id: string;
  clientId: number;
  clientName: string;
  transactionId: string;
  amount: number;
  date: string;
  severity: FraudSeverity;
  reason: string;
  status: FraudStatus;
}

export interface FraudStats {
  totalAlerts: number;
  criticalAlerts: number;
  resolvedToday: number;
  averageRiskScore: number;
  newAlerts: number;
}

export interface FraudFilters {
  period: "jour" | "mois" | "année" | "tout";
  severity?: FraudSeverity | "all";
  status?: FraudStatus | "all";
  search?: string;
}
