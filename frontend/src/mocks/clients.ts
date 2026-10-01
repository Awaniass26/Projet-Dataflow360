/**
 * Données mockées — Clients inscrits via le formulaire de scoring
 */

import type { Client, ClientDetail } from "@/types/client";

export const mockClients: Client[] = [
  {
    id: 1, name: "Awa Diop", phone: "+221 77 123 45 67", email: "awa.diop@email.com",
    score: 742, risk: "faible", registeredAt: "2026-09-15T10:00:00", lastActivity: "2026-09-28T14:22:00",
    totalTransactions: 156, averageAmount: 28500, city: "Dakar", accountAgeMonths: 24,
  },
  {
    id: 2, name: "Moussa Traoré", phone: "+221 76 987 65 43", email: "moussa.t@email.com",
    score: 418, risk: "élevé", registeredAt: "2026-09-20T09:30:00", lastActivity: "2026-09-29T09:15:00",
    totalTransactions: 43, averageAmount: 87500, city: "Thiès", accountAgeMonths: 6,
  },
  {
    id: 3, name: "Fatou Ndiaye", phone: "+221 78 555 12 34",
    score: 615, risk: "moyen", registeredAt: "2026-09-18T14:00:00", lastActivity: "2026-09-30T08:05:00",
    totalTransactions: 89, averageAmount: 31200, city: "Dakar", accountAgeMonths: 18,
  },
  {
    id: 4, name: "Ibrahima Sarr", phone: "+221 77 444 33 22", email: "ibrahima.sarr@email.com",
    score: 801, risk: "faible", registeredAt: "2026-09-10T11:20:00", lastActivity: "2026-09-29T18:40:00",
    totalTransactions: 210, averageAmount: 19800, city: "Saint-Louis", accountAgeMonths: 36,
  },
  {
    id: 5, name: "Mariama Ba", phone: "+221 76 111 22 33",
    score: 355, risk: "élevé", registeredAt: "2026-09-25T16:45:00", lastActivity: "2026-09-27T11:30:00",
    totalTransactions: 28, averageAmount: 125000, city: "Kaolack", accountAgeMonths: 3,
  },
  {
    id: 6, name: "Ousmane Fall", phone: "+221 77 888 99 00",
    score: 690, risk: "faible", registeredAt: "2026-09-12T08:00:00", lastActivity: "2026-09-28T12:00:00",
    totalTransactions: 134, averageAmount: 22000, city: "Dakar", accountAgeMonths: 20,
  },
  {
    id: 7, name: "Aissatou Sy", phone: "+221 78 222 33 44",
    score: 520, risk: "moyen", registeredAt: "2026-09-22T13:15:00", lastActivity: "2026-09-29T17:00:00",
    totalTransactions: 67, averageAmount: 45000, city: "Ziguinchor", accountAgeMonths: 12,
  },
  {
    id: 8, name: "Cheikh Gueye", phone: "+221 76 333 44 55",
    score: 780, risk: "faible", registeredAt: "2026-09-08T09:00:00", lastActivity: "2026-09-30T07:30:00",
    totalTransactions: 198, averageAmount: 17500, city: "Dakar", accountAgeMonths: 30,
  },
  {
    id: 9, name: "Khady Mbaye", phone: "+221 77 666 77 88",
    score: 445, risk: "élevé", registeredAt: "2026-09-28T10:30:00", lastActivity: "2026-09-29T20:00:00",
    totalTransactions: 35, averageAmount: 98000, city: "Mbour", accountAgeMonths: 4,
  },
  {
    id: 10, name: "Modou Diagne", phone: "+221 78 999 00 11",
    score: 655, risk: "moyen", registeredAt: "2026-09-14T15:00:00", lastActivity: "2026-09-28T11:45:00",
    totalTransactions: 102, averageAmount: 26800, city: "Rufisque", accountAgeMonths: 15,
  },
];

export const mockClientDetail: ClientDetail = {
  ...mockClients[0],
  explanation:
    "Le score de crédit de Awa Diop est élevé grâce à une activité régulière (156 transactions), des montants moyens stables et une faible volatilité des soldes. Les principaux facteurs positifs sont la fréquence des dépôts, l'ancienneté du compte (24 mois) et le faible taux de transactions échouées.",
  scoreHistory: [
    { date: "Avr", score: 680 },
    { date: "Mai", score: 695 },
    { date: "Juin", score: 710 },
    { date: "Juil", score: 725 },
    { date: "Août", score: 735 },
    { date: "Sept", score: 742 },
  ],
  recentTransactions: [
    { id: "TX-1001", date: "2026-09-28T14:22:00", type: "dépôt", amount: 25000, status: "réussi" },
    { id: "TX-1002", date: "2026-09-27T10:15:00", type: "paiement", amount: 8500, status: "réussi" },
    { id: "TX-1003", date: "2026-09-26T16:40:00", type: "transfert", amount: 15000, status: "réussi" },
    { id: "TX-1004", date: "2026-09-25T09:10:00", type: "retrait", amount: 20000, status: "réussi" },
    { id: "TX-1005", date: "2026-09-24T18:00:00", type: "dépôt", amount: 50000, status: "réussi" },
  ],
  kpis: {
    depositFrequency: 12,
    withdrawalFrequency: 8,
    averageBalance: 145000,
    failedTransactions: 2,
    uniqueCounterparties: 34,
  },
};
