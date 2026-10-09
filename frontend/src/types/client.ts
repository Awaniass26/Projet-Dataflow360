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

/** Payload formulaire → POST /credit/score (features calculées côté backend). */
export interface CreditScoreFormInput {
  account_id: string;
  age: number;
  montant_credit_demande: number;
  duree_credit_demande: number;
  type_activite: string;
  application_id?: string;
}

export interface CreditScoreResponse {
  application_id: string;
  risk_score: number | null;
  risk_level: "low" | "medium" | "high" | null;
  eligible: boolean | null;
  status: "completed" | "simulated";
  is_simulation: boolean;
  message: string;
  explanation_factors: string[] | null;
}