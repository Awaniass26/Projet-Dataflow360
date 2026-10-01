/**
 * Données mockées — Alertes de fraude
 */

import type { FraudAlert, FraudStats } from "@/types/fraud";

export const mockFraudAlerts: FraudAlert[] = [
  { id: "FA-001", clientId: 2, clientName: "Moussa Traoré", transactionId: "TX-2045", amount: 450000, date: "2026-09-30T07:12:00", severity: "critique", reason: "Montant anormalement élevé par rapport à l'historique du client", status: "nouvelle" },
  { id: "FA-002", clientId: 5, clientName: "Mariama Ba", transactionId: "TX-1987", amount: 180000, date: "2026-09-29T22:45:00", severity: "haute", reason: "Série de retraits rapides en moins de 10 minutes", status: "en_cours" },
  { id: "FA-003", clientId: 3, clientName: "Fatou Ndiaye", transactionId: "TX-1876", amount: 75000, date: "2026-09-29T15:30:00", severity: "moyenne", reason: "Transaction effectuée depuis une localisation inhabituelle", status: "nouvelle" },
  { id: "FA-004", clientId: 2, clientName: "Moussa Traoré", transactionId: "TX-1765", amount: 320000, date: "2026-09-28T11:20:00", severity: "haute", reason: "Changement soudain du pattern de transactions", status: "résolue" },
  { id: "FA-005", clientId: 9, clientName: "Khady Mbaye", transactionId: "TX-2100", amount: 95000, date: "2026-09-30T09:00:00", severity: "moyenne", reason: "Multiple tentatives de transfert vers le même destinataire", status: "nouvelle" },
  { id: "FA-006", clientId: 5, clientName: "Mariama Ba", transactionId: "TX-1650", amount: 210000, date: "2026-09-27T03:15:00", severity: "critique", reason: "Activité nocturne inhabituelle avec montants élevés", status: "en_cours" },
  { id: "FA-007", clientId: 7, clientName: "Aissatou Sy", transactionId: "TX-1540", amount: 42000, date: "2026-09-26T14:00:00", severity: "basse", reason: "Légère anomalie sur la fréquence des paiements", status: "fausse_alerte" },
  { id: "FA-008", clientId: 9, clientName: "Khady Mbaye", transactionId: "TX-1430", amount: 150000, date: "2026-09-25T19:30:00", severity: "haute", reason: "Nouveau device + montant élevé le même jour", status: "résolue" },
];

export const mockFraudStats: FraudStats = {
  totalAlerts: 47,
  criticalAlerts: 8,
  resolvedToday: 12,
  averageRiskScore: 62,
  newAlerts: 5,
};
