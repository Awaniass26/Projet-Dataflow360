/**
 * Types alignés sur l'API FastAPI.
 */

export interface Client {
  client_id: string;
  age: number;
  sexe: string;
  region: string;
  account_type: string;
}

export interface ClientTransaction {
  transaction_id: string;
  amount: number;
  type: string;
  channel: string;
  occurred_at: string;
}

export interface ClientCreditApplication {
  application_id: string;
  requested_amount: number;
  duration: number;
  income: number;
  expenses: number;
}

export interface ClientDetail extends Client {
  transactions: ClientTransaction[];
  credit_applications: ClientCreditApplication[];
}

/**
 * Données réellement attendues par POST /credit/score
 */
export interface CreditApplicationInput {
  application_id: string;
  account_id: string;
  requested_amount: number;
  requested_duration_months: number;
  estimated_monthly_income?: number;
  estimated_monthly_expenses?: number;
  monthly_transaction_volume?: number;
  monthly_transaction_frequency?: number;
  repayment_history_score?: number;
}

/**
 * Réponse de POST /credit/score
 */
export interface CreditScoreResponse {
  application_id: string;
  risk_score: number | null;
  risk_level: "low" | "medium" | "high" | null;
  status: "completed" | "simulated";
  is_simulation: boolean;
  message: string;
  explanation_factors: string[] | null;
}