import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";

import { Header } from "@/components/layout/Header";
import {
  Loading,
  ErrorMessage,
} from "@/components/ui/Loading";
import { useClients } from "@/hooks/useClients";

const PAGE_SIZE = 10;

export function ClientsPage() {
  const {
    data: clients,
    isLoading,
    error,
  } = useClients(100);

  const [search, setSearch] = useState("");
  const [visibleCount, setVisibleCount] =
    useState(PAGE_SIZE);

  // Debug temporaire : permet de vérifier
  // ce que React reçoit réellement de l'API.
  console.log("CLIENTS =", clients);
  console.log("LOADING =", isLoading);
  console.log("ERROR =", error);

  const filtered = useMemo(() => {
    if (!clients) {
      return [];
    }

    const query = search
      .trim()
      .toLowerCase();

    if (!query) {
      return clients;
    }

    return clients.filter((client) =>
      [
        client.client_id,
        client.region,
        client.account_type,
        client.sexe,
        String(client.age),
      ]
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [clients, search]);

  const visible = filtered.slice(
    0,
    visibleCount
  );

  const hasMore =
    visibleCount < filtered.length;

  if (isLoading) {
    return (
      <Loading message="Chargement des clients..." />
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message="Impossible de charger les clients."
      />
    );
  }

  if (!clients) {
    return (
      <ErrorMessage
        message="Aucune donnée client reçue."
      />
    );
  }

  return (
    <div>
      <Header
        title="Clients"
        subtitle={`${filtered.length} client(s)`}
      />

      <div className="mb-6">
        <div className="relative max-w-xl">
          <Search
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
          />

          <input
            type="text"
            placeholder="Rechercher un client, une région..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setVisibleCount(PAGE_SIZE);
            }}
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Client
                </th>

                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Âge
                </th>

                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Sexe
                </th>

                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Région
                </th>

                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Compte
                </th>

                <th className="px-6 py-3" />
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-200 bg-white">
              {visible.map((client) => (
                <tr
                  key={client.client_id}
                  className="transition-colors hover:bg-gray-50"
                >
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="font-medium text-gray-900">
                      {client.client_id}
                    </div>
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {client.age}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {client.sexe}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {client.region}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {client.account_type}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <Link
                      to={`/clients/${client.client_id}`}
                      className="font-medium text-primary-600 hover:text-primary-800"
                    >
                      Voir
                    </Link>
                  </td>
                </tr>
              ))}

              {visible.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-12 text-center text-sm text-gray-500"
                  >
                    Aucun client trouvé.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {hasMore && (
          <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 text-center">
            <button
              type="button"
              onClick={() =>
                setVisibleCount(
                  (value) => value + PAGE_SIZE
                )
              }
              className="text-sm font-medium text-primary-600 hover:text-primary-800"
            >
              Voir plus
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
