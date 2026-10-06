import { useQuery } from "@tanstack/react-query";

import {
  getClients,
  getClientById,
} from "@/services/clients";

export function useClients(limit = 50) {
  return useQuery({
    queryKey: ["clients", limit],
    queryFn: () => getClients(limit),
  });
}

export function useClient(clientId: string | undefined) {
  return useQuery({
    queryKey: ["clients", clientId],
    queryFn: () => getClientById(clientId as string),
    enabled: Boolean(clientId),
  });
}