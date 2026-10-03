/**
 * Service Clients
 * Appels FastAPI réels via l'instance Axios centrale
 */

import type { Client, ClientDetail, ScoringFormData } from "@/types/client";
import api from "./api";

/**
 * Récupère la liste de tous les clients
 * GET /api/clients
 */
export async function getClients(): Promise<Client[]> {
  const { data } = await api.get<Client[]>("/api/clients");
  return data;
}

/**
 * Récupère le détail d'un client (score, historique, KPIs, transactions)
 * GET /api/clients/{id}
 */
export async function getClientById(id: number): Promise<ClientDetail> {
  const { data } = await api.get<ClientDetail>(`/api/clients/${id}`);
  return data;
}

/**
 * Soumet le formulaire de scoring crédit
 * POST /api/scoring
 *
 * Body : ScoringFormData
 * Response : { success: boolean; score: number; clientId: number }
 */
export async function submitScoringForm(
  data: ScoringFormData
): Promise<{ success: boolean; score: number; clientId: number }> {
  const { data: result } = await api.post<{
    success: boolean;
    score: number;
    clientId: number;
  }>("/api/scoring", data);
  return result;
}