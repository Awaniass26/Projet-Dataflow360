import { Link, useParams } from "react-router-dom";

import { Header } from "@/components/layout/Header";
import { Card, CardTitle, CardValue } from "@/components/ui/Card";
import { Loading, ErrorMessage } from "@/components/ui/Loading";
import { useClient } from "@/hooks/useClients";
import { formatAmount } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

export function ClientDetailPage() {
  const { id } = useParams<{
    id: string;
  }>();

  const {
    data: client,
    isLoading,
    error,
  } = useClient(id);

  if (isLoading) {
    return (
      <Loading message="Chargement du client..." />
    );
  }

  if (error || !client) {
    return (
      <ErrorMessage message="Client introuvable." />
    );
  }

  return (
    <div>
      <Link
        to="/clients"
        className="mb-4 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        <ArrowLeft className="h-4 w-4" />
        Retour aux clients
      </Link>

      <Header
        title={client.client_id}
        subtitle={`Client ${client.client_id}`}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card>
          <CardTitle>Identifiant</CardTitle>
          <CardValue className="text-2xl">
            {client.client_id}
          </CardValue>
        </Card>

        <Card>
          <CardTitle>Âge</CardTitle>
          <CardValue>
            {client.age}
          </CardValue>
        </Card>

        <Card>
          <CardTitle>Sexe</CardTitle>
          <CardValue>
            {client.sexe}
          </CardValue>
        </Card>

        <Card className="lg:col-span-3">
          <h3 className="mb-4 text-base font-semibold text-gray-900">
            Informations du compte
          </h3>

          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-sm text-gray-500">
                Région
              </dt>

              <dd className="mt-1 font-medium text-gray-900">
                {client.region}
              </dd>
            </div>

            <div>
              <dt className="text-sm text-gray-500">
                Type de compte
              </dt>

              <dd className="mt-1 font-medium text-gray-900">
                {client.account_type}
              </dd>
            </div>

            <div>
              <dt className="text-sm text-gray-500">
                Nombre de transactions
              </dt>

              <dd className="mt-1 font-medium text-gray-900">
                {client.transactions.length}
              </dd>
            </div>
          </dl>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="mb-4 text-base font-semibold text-gray-900">
            Transactions
          </h3>

          {client.transactions.length === 0 ? (
            <p className="text-sm text-gray-500">
              Aucune transaction.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b">
                    <th className="px-3 py-2 text-left text-xs text-gray-500">
                      ID
                    </th>
                    <th className="px-3 py-2 text-left text-xs text-gray-500">
                      Type
                    </th>
                    <th className="px-3 py-2 text-left text-xs text-gray-500">
                      Canal
                    </th>
                    <th className="px-3 py-2 text-right text-xs text-gray-500">
                      Montant
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {client.transactions.map(
                    (transaction) => (
                      <tr
                        key={
                          transaction.transaction_id
                        }
                        className="border-b"
                      >
                        <td className="px-3 py-3 text-sm">
                          {transaction.transaction_id}
                        </td>

                        <td className="px-3 py-3 text-sm">
                          {transaction.type}
                        </td>

                        <td className="px-3 py-3 text-sm">
                          {transaction.channel}
                        </td>

                        <td className="px-3 py-3 text-right text-sm font-medium">
                          {formatAmount(
                            transaction.amount
                          )}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="mb-4 text-base font-semibold text-gray-900">
            Demandes de crédit
          </h3>

          {client.credit_applications.length ===
          0 ? (
            <p className="text-sm text-gray-500">
              Aucune demande de crédit.
            </p>
          ) : (
            <div className="space-y-4">
              {client.credit_applications.map(
                (application) => (
                  <div
                    key={
                      application.application_id
                    }
                    className="rounded-lg border p-4"
                  >
                    <p className="text-sm font-medium">
                      {application.application_id}
                    </p>

                    <p className="mt-2 text-sm text-gray-600">
                      Montant :{" "}
                      {formatAmount(
                        application.requested_amount
                      )}
                    </p>

                    <p className="text-sm text-gray-600">
                      Durée :{" "}
                      {application.duration} mois
                    </p>

                    <p className="text-sm text-gray-600">
                      Revenus :{" "}
                      {formatAmount(
                        application.income
                      )}
                    </p>

                    <p className="text-sm text-gray-600">
                      Dépenses :{" "}
                      {formatAmount(
                        application.expenses
                      )}
                    </p>
                  </div>
                )
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}