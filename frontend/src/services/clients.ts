/**
 * Service Clients — appels vers l'API FastAPI
 * ===========================================
 * Ces fonctions remplacent les anciens mocks.
 * Elles appellent les endpoints /api/clients et /api/scoring du backend.
 */
import api from "./api";
import type { Client, ClientDetail, ScoringFormData } from "@/types/client";

/** Récupère la liste des clients (scores + activité) */
export async function getClients(): Promise<Client[]> {
  const { data } = await api.get<Client[]>("clients");
  return data;
}

/** Fiche détaillée d'un client (id numérique = suffixe de CL000001) */
export async function getClientById(id: number): Promise<ClientDetail> {
  const { data } = await api.get<ClientDetail>(`clients/${id}`);
  return data;
}

/** Envoie le formulaire de scoring crédit et récupère le score calculé */
export async function submitScoringForm(
  formData: ScoringFormData
): Promise<{ success: boolean; score: number; clientId: number }> {
  const { data } = await api.post<{ success: boolean; score: number; clientId: number }>(
    "scoring",
    formData
  );
  return data;
}
