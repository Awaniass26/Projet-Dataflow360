/**
 * Hooks React Query pour les clients
 * Centralise le fetching + cache + états de chargement
 */

import { useQuery } from "@tanstack/react-query";
import { getClients, getClientById } from "@/services/clients";

export function useClients() {
  return useQuery({
    queryKey: ["clients"],
    queryFn: getClients,
  });
}

export function useClient(id: number) {
  return useQuery({
    queryKey: ["clients", id],
    queryFn: () => getClientById(id),
    enabled: !!id, // ne lance la requête que si l'id est valide
  });
}
