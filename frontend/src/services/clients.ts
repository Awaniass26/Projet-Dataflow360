/**
 * Services Clients / Crédit
 * GET /clients renvoie une réponse paginée : { items, page, page_size, total, total_pages }
 */

import api from "./api";

import type {
  Client,
  ClientDetail,
  ClientListResponse,
  CreditApplicationInput,
  CreditScoreResponse,
} from "@/types/client";

/**
 * GET /clients — retourne uniquement la liste des clients
 */
export async function getClients(limit = 50): Promise<Client[]> {
  const pageSize = Math.min(Math.max(limit, 1), 100);

  const { data } = await api.get<ClientListResponse>("/clients", {
    params: {
      page: 1,
      page_size: pageSize,
    },
  });

  // L'API renvoie un objet paginé, pas un tableau brut
  return data.items ?? [];
}

/**
 * GET /clients/{client_id}
 */
export async function getClientById(
  clientId: string
): Promise<ClientDetail> {
  const { data } = await api.get<ClientDetail>(
    `/clients/${encodeURIComponent(clientId)}`
  );
  return data;
}

/**
 * POST /credit/score
 */
export async function submitCreditScore(
  application: CreditApplicationInput
): Promise<CreditScoreResponse> {
  const { data } = await api.post<CreditScoreResponse>(
    "/credit/score",
    application
  );
  return data;
}

/**
 * GET /credit/score/{application_id}
 */
export async function getCreditScore(
  applicationId: string
): Promise<CreditScoreResponse> {
  const { data } = await api.get<CreditScoreResponse>(
    `/credit/score/${encodeURIComponent(applicationId)}`
  );
  return data;
}