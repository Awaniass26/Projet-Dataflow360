/**
 * Page Détail client — score, KPI, explication IA, historique
 */

import { useParams, Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Card, CardTitle, CardValue } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import { useClient } from "@/hooks/useClients";
import { formatAmount } from "@/lib/utils";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { ArrowLeft } from "lucide-react";

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const clientId = Number(id);
  const { data: client, isLoading, error } = useClient(clientId);

  if (isLoading) return <Loading message="Chargement du client..." />;
  if (error || !client) return <ErrorMessage message="Client introuvable." />;

  return (
    <div>
      <Link to="/clients" className="mb-4 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800">
        <ArrowLeft className="h-4 w-4" />
        Retour à l'historique
      </Link>

      <Header
        title={client.name}
        subtitle={client.phone}
        actions={<Badge variant="risk" value={client.risk} className="text-sm px-3 py-1">Risque {client.risk}</Badge>}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Score */}
        <Card className="flex flex-col items-center justify-center text-center">
          <p className="text-sm font-medium text-gray-500">Score de crédit</p>
          <p className="mt-2 text-5xl font-bold text-primary-600">{client.score}</p>
          <p className="mt-2 text-sm text-gray-400">sur 1000</p>
        </Card>

        {/* Infos */}
        <Card className="lg:col-span-2">
          <h3 className="mb-4 text-base font-semibold text-gray-900">Informations</h3>
          <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-gray-500">Ville</dt>
              <dd className="mt-1 font-medium text-gray-900">{client.city || "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Ancienneté compte</dt>
              <dd className="mt-1 font-medium text-gray-900">{client.accountAgeMonths ? `${client.accountAgeMonths} mois` : "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Inscription scoring</dt>
              <dd className="mt-1 font-medium text-gray-900">
                {new Date(client.registeredAt).toLocaleDateString("fr-FR")}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Transactions</dt>
              <dd className="mt-1 font-medium text-gray-900">{client.totalTransactions}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Montant moyen</dt>
              <dd className="mt-1 font-medium text-gray-900">{formatAmount(client.averageAmount)}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Email</dt>
              <dd className="mt-1 font-medium text-gray-900">{client.email || "—"}</dd>
            </div>
          </dl>
        </Card>

        {/* KPI client */}
        <Card className="lg:col-span-3">
          <h3 className="mb-4 text-base font-semibold text-gray-900">KPI comportementaux</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            <div className="rounded-lg bg-gray-50 p-4 text-center">
              <CardTitle>Dépôts / mois</CardTitle>
              <CardValue className="text-2xl">{client.kpis.depositFrequency}</CardValue>
            </div>
            <div className="rounded-lg bg-gray-50 p-4 text-center">
              <CardTitle>Retraits / mois</CardTitle>
              <CardValue className="text-2xl">{client.kpis.withdrawalFrequency}</CardValue>
            </div>
            <div className="rounded-lg bg-gray-50 p-4 text-center">
              <CardTitle>Solde moyen</CardTitle>
              <CardValue className="text-xl">{formatAmount(client.kpis.averageBalance)}</CardValue>
            </div>
            <div className="rounded-lg bg-gray-50 p-4 text-center">
              <CardTitle>Tx échouées</CardTitle>
              <CardValue className="text-2xl">{client.kpis.failedTransactions}</CardValue>
            </div>
            <div className="rounded-lg bg-gray-50 p-4 text-center">
              <CardTitle>Contreparties</CardTitle>
              <CardValue className="text-2xl">{client.kpis.uniqueCounterparties}</CardValue>
            </div>
          </div>
        </Card>

        {/* Explication IA */}
        <Card className="lg:col-span-3">
          <h3 className="mb-3 text-base font-semibold text-gray-900">Explication du score (IA)</h3>
          <p className="text-sm leading-relaxed text-gray-700">{client.explanation}</p>
        </Card>

        {/* Historique score */}
        {client.scoreHistory.length > 0 && (
          <Card className="lg:col-span-2">
            <h3 className="mb-4 text-base font-semibold text-gray-900">Évolution du score</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={client.scoreHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis domain={["dataMin - 30", "dataMax + 30"]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        )}

        {/* Transactions */}
        {client.recentTransactions.length > 0 && (
          <Card>
            <h3 className="mb-4 text-base font-semibold text-gray-900">Transactions récentes</h3>
            <ul className="space-y-3">
              {client.recentTransactions.map((tx) => (
                <li key={tx.id} className="flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium text-gray-900 capitalize">{tx.type}</p>
                    <p className="text-gray-500">{new Date(tx.date).toLocaleDateString("fr-FR")}</p>
                  </div>
                  <span className="font-medium text-gray-900">{formatAmount(tx.amount)}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </div>
  );
}
