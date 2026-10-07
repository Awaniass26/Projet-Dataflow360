/**
 * Types alignés sur l'API FastAPI /clients et /credit
 */

export interface Client {
  client_id: string;
  name: string;
  age: number;
  sexe: string;
  region: string;
  account_type: string;
}

export interface ClientListResponse {
  items: Client[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
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

export interface CreditScoreResponse {
  application_id: string;
  risk_score: number | null;
  risk_level: "low" | "medium" | "high" | null;
  status: "completed" | "simulated";
  is_simulation: boolean;
  message: string;
  explanation_factors: string[] | null;
}