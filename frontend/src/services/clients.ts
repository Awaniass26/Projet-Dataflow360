/**
 * Service Clients
 * Mode mock pour l'instant — remplacer par les appels FastAPI plus tard
 */

import type { Client, ClientDetail, ScoringFormData } from "@/types/client";
import { mockClients, mockClientDetail } from "@/mocks/clients";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getClients(): Promise<Client[]> {
  await delay(400);
  return mockClients;
}

export async function getClientById(id: number): Promise<ClientDetail> {
  await delay(300);
  if (id === 1) return mockClientDetail;
  const client = mockClients.find((c) => c.id === id);
  if (!client) throw new Error("Client introuvable");
  return {
    ...client,
    explanation: `Score calculé à partir de l'historique transactionnel de ${client.name}. Facteurs principaux : fréquence des opérations, montants moyens et ancienneté du compte.`,
    scoreHistory: [
      { date: "Juil", score: Math.max(300, client.score - 40) },
      { date: "Août", score: Math.max(300, client.score - 20) },
      { date: "Sept", score: client.score },
    ],
    recentTransactions: [],
    kpis: {
      depositFrequency: Math.floor(Math.random() * 15) + 3,
      withdrawalFrequency: Math.floor(Math.random() * 10) + 2,
      averageBalance: client.averageAmount * 5,
      failedTransactions: Math.floor(Math.random() * 5),
      uniqueCounterparties: Math.floor(Math.random() * 40) + 5,
    },
  };
}

/**
 * Soumet le formulaire de scoring
 * En mode mock : simule un score et retourne un succès
 */
export async function submitScoringForm(data: ScoringFormData): Promise<{ success: boolean; score: number; clientId: number }> {
  await delay(800);
  // Simulation simple d'un score basé sur les données du formulaire
  let score = 400;
  if (data.accountAgeMonths > 12) score += 100;
  if (data.accountAgeMonths > 24) score += 50;
  if (data.averageMonthlyDeposit > 50000) score += 80;
  if (data.totalTransactionsLast3Months > 30) score += 70;
  if (data.hasLoanHistory) score += 40;
  score = Math.min(950, score + Math.floor(Math.random() * 50));

  return { success: true, score, clientId: mockClients.length + 1 };
}
