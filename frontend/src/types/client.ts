/**
 * Types liés aux clients et au scoring crédit
 */

export type RiskLevel = "faible" | "moyen" | "élevé";

/** Client issu du formulaire de scoring */
export interface Client {
  id: number;
  name: string;
  phone: string;
  email?: string;
  score: number;
  risk: RiskLevel;
  /** Date d'inscription au scoring */
  registeredAt: string;
  lastActivity: string;
  totalTransactions: number;
  averageAmount: number;
  city?: string;
  accountAgeMonths?: number;
}

export interface ClientDetail extends Client {
  explanation: string;
  scoreHistory: ScoreHistoryItem[];
  recentTransactions: Transaction[];
  kpis: ClientKPIs;
}

export interface ClientKPIs {
  depositFrequency: number;
  withdrawalFrequency: number;
  averageBalance: number;
  failedTransactions: number;
  uniqueCounterparties: number;
}

export interface ScoreHistoryItem {
  date: string;
  score: number;
}

export interface Transaction {
  id: string;
  date: string;
  type: "dépôt" | "retrait" | "transfert" | "paiement";
  amount: number;
  status: "réussi" | "échoué" | "en_attente";
}

/** Données du formulaire d'inscription scoring */
export interface ScoringFormData {
  firstName: string;
  lastName: string;
  phone: string;
  email?: string;
  city: string;
  accountAgeMonths: number;
  averageMonthlyDeposit: number;
  averageMonthlyWithdrawal: number;
  totalTransactionsLast3Months: number;
  hasLoanHistory: boolean;
  occupation: string;
}
