import api from "./api";
import type {
  Client,
  ClientDetail,
  ClientListResponse,
  CreditApplicationInput,
  CreditScoreResponse,
} from "@/types/client";

export async function getClients(limit = 50): Promise<Client[]> {
  const pageSize = Math.min(Math.max(limit, 1), 100);
  const { data } = await api.get<ClientListResponse>("/clients", {
    params: { page: 1, page_size: pageSize },
  });
  return data.items ?? [];
}

export async function getClientById(clientId: string): Promise<ClientDetail> {
  const { data } = await api.get<ClientDetail>(
    `/clients/${encodeURIComponent(clientId)}`
  );
  return data;
}

export async function submitCreditScore(
  application: CreditApplicationInput
): Promise<CreditScoreResponse> {
  const { data } = await api.post<CreditScoreResponse>(
    "/credit/score",
    application
  );
  return data;
}

export async function getCreditScore(
  applicationId: string
): Promise<CreditScoreResponse> {
  const { data } = await api.get<CreditScoreResponse>(
    `/credit/score/${encodeURIComponent(applicationId)}`
  );
  return data;
}
