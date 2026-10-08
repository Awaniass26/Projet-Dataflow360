import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardTitle, CardValue, KpiCard } from "@/components/ui/Card";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import { useClient } from "@/hooks/useClients";
import { formatAmount } from "@/lib/utils";

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: client, isLoading, error } = useClient(id);

  if (isLoading) return <Loading message="Chargement du client..." />;
  if (error || !client) return <ErrorMessage message="Client introuvable." />;

  const totalTx = client.transactions?.length ?? 0;
  const totalCredits = client.credit_applications?.length ?? 0;
  const volume = (client.transactions ?? []).reduce(
    (sum, t) => sum + (t.amount ?? 0),
    0
  );

  return (
    <div>
      <Link
        to="/clients"
        className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-slate-500 hover:text-slate-800"
      >
        <ArrowLeft className="h-4 w-4" />
        Retour aux clients
      </Link>

      <PageHeader
        title={client.name || client.client_id}
        subtitle={`Identifiant ${client.client_id}`}
      />

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Âge" value={client.age} />
        <KpiCard title="Région" value={client.region} accent="gold" />
        <KpiCard title="Transactions" value={totalTx} accent="green" />
        <KpiCard title="Volume" value={formatAmount(volume)} accent="blue" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card>
          <CardTitle>Profil</CardTitle>
          <div className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Sexe</span>
              <span className="font-medium">{client.sexe}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Type de compte</span>
              <span className="font-medium">{client.account_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Crédits</span>
              <span className="font-medium">{totalCredits}</span>
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardTitle>Dernières transactions</CardTitle>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="pb-2 pr-4">ID</th>
                  <th className="pb-2 pr-4">Type</th>
                  <th className="pb-2 pr-4">Canal</th>
                  <th className="pb-2 text-right">Montant</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(client.transactions ?? []).slice(0, 8).map((tx) => (
                  <tr key={tx.transaction_id}>
                    <td className="py-2 pr-4 font-mono text-xs text-slate-500">
                      {tx.transaction_id}
                    </td>
                    <td className="py-2 pr-4">{tx.type}</td>
                    <td className="py-2 pr-4">{tx.channel}</td>
                    <td className="py-2 text-right font-medium">
                      {formatAmount(tx.amount)}
                    </td>
                  </tr>
                ))}
                {(client.transactions ?? []).length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-slate-400">
                      Aucune transaction
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {(client.credit_applications ?? []).length > 0 && (
        <Card className="mt-6">
          <CardTitle>Demandes de crédit</CardTitle>
          <CardValue className="!text-base !font-medium text-slate-500">
            {totalCredits} demande(s)
          </CardValue>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="pb-2 pr-4">ID</th>
                  <th className="pb-2 pr-4">Montant</th>
                  <th className="pb-2 pr-4">Durée</th>
                  <th className="pb-2 pr-4">Revenus</th>
                  <th className="pb-2">Dépenses</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {client.credit_applications.map((app) => (
                  <tr key={app.application_id}>
                    <td className="py-2 pr-4 font-mono text-xs">{app.application_id}</td>
                    <td className="py-2 pr-4">{formatAmount(app.requested_amount)}</td>
                    <td className="py-2 pr-4">{app.duration} mois</td>
                    <td className="py-2 pr-4">{formatAmount(app.income)}</td>
                    <td className="py-2">{formatAmount(app.expenses)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
