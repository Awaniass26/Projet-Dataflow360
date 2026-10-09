import { useQuery } from "@tanstack/react-query";
import { getClients, getClientById } from "@/services/clients";

const REFRESH_INTERVAL = 5000;

export function useClients(limit = 50) {
  return useQuery({
    queryKey: ["clients", limit],
    queryFn: () => getClients(limit),
    refetchInterval: REFRESH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

export function useClient(clientId: string | undefined) {
  return useQuery({
    queryKey: ["clients", clientId],
    queryFn: () => getClientById(clientId as string),
    enabled: Boolean(clientId),
    refetchInterval: REFRESH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}