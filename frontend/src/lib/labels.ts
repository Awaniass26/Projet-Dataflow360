import type { FraudStatus, RiskLevel } from "@/types/fraud";

export const RISK_LABELS: Record<RiskLevel, string> = {
  low: "Faible",
  medium: "Moyen",
  high: "Élevé",
};

export const STATUS_LABELS: Record<FraudStatus, string> = {
  pending: "En attente",
  confirmed: "Fraude confirmée",
  dismissed: "Fausse alerte",
};

export const RISK_LEVELS: RiskLevel[] = ["low", "medium", "high"];

export const FRAUD_STATUSES: FraudStatus[] = [
  "pending",
  "confirmed",
  "dismissed",
];

export const ROLE_LABELS: Record<string, string> = {
  admin: "Administrateur",
  analyst: "Analyste",
};
