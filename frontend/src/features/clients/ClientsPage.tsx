import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import { useClients } from "@/hooks/useClients";

const PAGE_SIZE = 10;

export function ClientsPage() {
  const { data: clients, isLoading, error } = useClients(100);
  const [search, setSearch] = useState("");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const filtered = useMemo(() => {
    if (!clients) return [];
    const query = search.trim().toLowerCase();
    if (!query) return clients;
    return clients.filter((client) =>
      [
        client.client_id,
        client.name,
        client.region,
        client.account_type,
        client.sexe,
        String(client.age),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [clients, search]);

  const visible = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  if (isLoading) return <Loading message="Chargement des clients..." />;
  if (error) return <ErrorMessage message="Impossible de charger les clients." />;
  if (!clients) return <ErrorMessage message="Aucune donnée client reçue." />;

  return (
    <div>
      <PageHeader
        title="Historiques Clients"
      />

      <div className="mb-6">
        <div className="relative max-w-xl">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setVisibleCount(PAGE_SIZE);
            }}
            placeholder="Rechercher un client, une région, un type de compte…"
            className="input-field pl-10"
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100">
            <thead className="bg-slate-50/80">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Client
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Âge
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Sexe
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Région
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Compte
                </th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visible.map((client) => (
                <tr key={client.client_id} className="transition hover:bg-slate-50/80">
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="font-semibold text-slate-900">
                      {client.name || client.client_id}
                    </div>
                    <div className="text-xs text-slate-400">{client.client_id}</div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600">
                    {client.age}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600">
                    {client.sexe}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600">
                    {client.region}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600">
                    {client.account_type}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <Link
                      to={`/clients/${client.client_id}`}
                      className="font-semibold text-brand-blue hover:text-primary-700"
                    >
                      Voir
                    </Link>
                  </td>
                </tr>
              ))}
              {visible.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-sm text-slate-500">
                    Aucun client trouvé.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {hasMore && (
          <div className="border-t border-slate-100 bg-slate-50/50 px-6 py-4 text-center">
            <button
              type="button"
              onClick={() => setVisibleCount((v) => v + PAGE_SIZE)}
              className="text-sm font-semibold text-brand-blue hover:text-primary-700"
            >
              Voir plus
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
