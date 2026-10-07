/**
 * Services Clients / Crédit
 *
 * Tous les endpoints correspondent au contrat FastAPI.
 */

import api from "./api";

import type {
  Client,
  ClientDetail,
  CreditApplicationInput,
  CreditScoreResponse,
} from "@/types/client";

/**
 * GET /clients
 */
export async function getClients(
  limit = 50
): Promise<Client[]> {
  const { data } = await api.get<Client[]>(
    "/clients",
    {
      params: { limit },
    }
  );

  return data;
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