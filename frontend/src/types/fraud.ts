export type RiskLevel = "low" | "medium" | "high";
export type FraudStatus = "pending" | "reviewed" | "confirmed" | "dismissed";

export interface FraudAlert {
  alert_id: number;
  transaction_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  status: FraudStatus;
  explanation: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  created_at: string;
}

export interface FraudAlertListResponse {
  items: FraudAlert[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface FraudEvolutionPoint {
  date: string;
  alert_count: number;
  suspicious_amount: number;
}

export interface FraudZonePoint {
  zone: string;
  alert_count: number;
  transaction_count: number;
  alert_rate: number;
}

export interface FraudStats {
  total_transactions: number;
  total_alerts: number;
  suspicious_rate: number;
  suspicious_amount: number;
  alerts_by_status: Record<string, number>;
  alerts_by_risk_level: Record<string, number>;
  alerts_evolution: FraudEvolutionPoint[];
  alerts_by_zone?: FraudZonePoint[];
}

export interface FraudAlertUpdate {
  status: FraudStatus;
  reviewed_by: string;
  explanation?: string;
}