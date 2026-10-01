/**
 * Page Historique des clients inscrits via le formulaire de scoring
 * - Filtres (recherche, risque)
 * - Affiche 5 clients puis scroll pour voir la suite
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Badge } from "@/components/ui/Badge";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import { useClients } from "@/hooks/useClients";
import { formatAmount } from "@/lib/utils";
import type { RiskLevel } from "@/types/client";
import { Search } from "lucide-react";

const PAGE_SIZE = 5;

export function ClientsPage() {
  const { data: clients, isLoading, error } = useClients();
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "all">("all");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const filtered = useMemo(() => {
    if (!clients) return [];
    return clients.filter((c) => {
      const matchSearch =
        !search ||
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.phone.includes(search) ||
        (c.city && c.city.toLowerCase().includes(search.toLowerCase()));
      const matchRisk = riskFilter === "all" || c.risk === riskFilter;
      return matchSearch && matchRisk;
    });
  }, [clients, search, riskFilter]);

  const visible = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  if (isLoading) return <Loading message="Chargement des clients..." />;
  if (error || !clients) return <ErrorMessage message="Impossible de charger les clients." />;

  return (
    <div>
      <Header
        title="Historique des clients"
        subtitle={`${filtered.length} client(s) inscrit(s) via le formulaire de scoring`}
      />

      {/* Filtres */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher par nom, téléphone, ville..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setVisibleCount(PAGE_SIZE);
            }}
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => {
            setRiskFilter(e.target.value as RiskLevel | "all");
            setVisibleCount(PAGE_SIZE);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          <option value="all">Tous les risques</option>
          <option value="faible">Faible</option>
          <option value="moyen">Moyen</option>
          <option value="élevé">Élevé</option>
        </select>
      </div>

      {/* Tableau */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Client</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Risque</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Ville</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Inscription</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Montant moyen</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {visible.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50 transition-colors">
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="font-medium text-gray-900">{client.name}</div>
                    <div className="text-sm text-gray-500">{client.phone}</div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span className="text-lg font-semibold text-gray-900">{client.score}</span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge variant="risk" value={client.risk}>{client.risk}</Badge>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">{client.city || "—"}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {new Date(client.registeredAt).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" })}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {formatAmount(client.averageAmount)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <Link to={`/clients/${client.id}`} className="font-medium text-primary-600 hover:text-primary-800">
                      Voir détail →
                    </Link>
                  </td>
                </tr>
              ))}
              {visible.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-sm text-gray-500">
                    Aucun client trouvé
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Bouton scroll / voir plus */}
        {hasMore && (
          <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 text-center">
            <button
              onClick={() => setVisibleCount((v) => v + PAGE_SIZE)}
              className="text-sm font-medium text-primary-600 hover:text-primary-800"
            >
              Voir plus ({filtered.length - visibleCount} restant{filtered.length - visibleCount > 1 ? "s" : ""})
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
