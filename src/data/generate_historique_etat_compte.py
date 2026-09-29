"""
src/data/generate_historique_etat_compte.py

Table 6/8 — Historique d'état de compte.
Point de cohérence important (validé avec le groupe) : le solde n'est PAS
inventé indépendamment, il est calculé comme le cumul réel des transactions
de chaque compte, jour par jour. Sinon cette table contredirait
transactions.csv.

Simplification assumée : dépôt/entrant = +montant, retrait/paiement/sortant
= -montant. On ignore volontairement les montants négatifs/nuls injectés
comme anomalies de qualité pour ce calcul (ils seront nettoyés en Sprint 2
de toute façon).
"""

import numpy as np
import pandas as pd


def generate_historique_etat_compte(comptes_df: pd.DataFrame,
                                     transactions_df: pd.DataFrame) -> pd.DataFrame:
    tx = transactions_df.copy()
    tx["montant"] = pd.to_numeric(tx["montant"], errors="coerce")
    tx = tx[tx["montant"] > 0]  # on ignore les lignes sales pour ce calcul dérivé
    tx["date"] = pd.to_datetime(tx["horodatage"], errors="coerce").dt.date
    tx = tx.dropna(subset=["date"])

    # signe du flux : entrant (+) pour le compte destinataire, sortant (-) pour l'émetteur
    flux_sortant = tx.groupby(["id_compte_emetteur", "date"])["montant"].sum().reset_index()
    flux_sortant.columns = ["id_compte", "date", "flux"]
    flux_sortant["flux"] = -flux_sortant["flux"]

    flux_entrant = tx[tx["id_compte_destinataire"] != ""].groupby(
        ["id_compte_destinataire", "date"]
    )["montant"].sum().reset_index()
    flux_entrant.columns = ["id_compte", "date", "flux"]

    flux = pd.concat([flux_sortant, flux_entrant], ignore_index=True)
    flux = flux.groupby(["id_compte", "date"])["flux"].sum().reset_index()
    flux = flux.sort_values(["id_compte", "date"])

    flux["solde_fin_journee"] = flux.groupby("id_compte")["flux"].cumsum()

    flux = flux.rename(columns={"date": "date"})[["id_compte", "date", "solde_fin_journee"]]
    return flux


if __name__ == "__main__":
    comptes = pd.read_csv("../../data/synthetic/comptes.csv")
    transactions = pd.read_csv("../../data/synthetic/transactions.csv")
    df = generate_historique_etat_compte(comptes, transactions)
    df.to_csv("../../data/synthetic/historique_etat_compte.csv", index=False)
    print(f"{len(df)} lignes (compte x jour) -> data/synthetic/historique_etat_compte.csv")