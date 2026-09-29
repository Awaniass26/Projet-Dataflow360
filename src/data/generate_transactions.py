"""
src/data/generate_transactions.py

Table 5/8 — Transactions. La table centrale du projet.

Deux types d'anomalies bien distincts et injectés indépendamment l'un de
l'autre (ne pas les confondre, voir discussion du groupe) :

1. FRAUDE (colonne `fraude`) : des scénarios COMBINÉS et réalistes, pas des
   règles isolées. Une transaction frauduleuse cumule en général plusieurs
   signaux faibles (nouvel appareil, nouveau destinataire, montant
   inhabituel) plutôt qu'un seul — avec une part de variabilité (2 signaux
   sur 3 en général, pas toujours les 3).

2. QUALITÉ (aucune colonne dédiée — c'est justement le travail du Sprint 2
   de les détecter) : valeurs manquantes, doublons, formats incohérents,
   valeurs impossibles. Injectées indépendamment de la fraude : une
   transaction "sale" n'est pas forcément frauduleuse, et vice-versa.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
AUJOURD_HUI = datetime(2026, 9, 24)

TYPES = ["transfert", "paiement", "retrait", "dépôt"]
POIDS_TYPES = [0.50, 0.30, 0.15, 0.05]
CANAUX = ["app", "USSD", "agent"]
POIDS_CANAUX = [0.55, 0.30, 0.15]

TAUX_FRAUDE = 0.025          # 2.5%
TAUX_ANOMALIE_QUALITE = 0.03  # 3%


def _tirer_montant_normal(rng, n):
    montants = rng.lognormal(mean=8.3, sigma=0.9, size=n)
    return np.clip(montants, 100, 300000).round(0)


def _tirer_heure_normale(rng, n):
    heures = rng.normal(loc=15, scale=4.5, size=n)
    return np.clip(heures, 0, 23).astype(int)


def generate_transactions(comptes_df: pd.DataFrame, appareils_df: pd.DataFrame,
                           n_transactions: int = 500_000,
                           seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_comptes = len(comptes_df)

    comptes_actifs = comptes_df[comptes_df["statut_compte"] == "actif"].reset_index(drop=True)
    n_comptes_actifs = len(comptes_actifs)

    n_fraude = int(n_transactions * TAUX_FRAUDE)
    n_normales = n_transactions - n_fraude

    # Index rapide : appareils disponibles par client
    appareils_par_client = appareils_df.groupby("id_client")["id_appareil"].apply(list).to_dict()

    def _tirer_lot(n, est_fraude: bool):
        idx_emetteurs = rng.integers(0, n_comptes_actifs, size=n)
        emetteurs = comptes_actifs.iloc[idx_emetteurs]
        ids_compte_emetteur = emetteurs["id_compte"].values
        ids_client_emetteur = emetteurs["id_client"].values
        zones = emetteurs["zone_habituelle"].values

        types_ = rng.choice(TYPES, size=n, p=POIDS_TYPES)
        canaux = rng.choice(CANAUX, size=n, p=POIDS_CANAUX)
        # Plage étendue à 730 jours (2 ans) pour couvrir la même période que
        # l'ancienneté des comptes et les dates d'octroi de crédit — sinon
        # un crédit ancien n'aurait aucun historique de transaction visible,
        # ce qui fausserait artificiellement le taux de défaut calculé.
        jours_offset = rng.integers(0, 730, size=n)

        # --- Destinataire (pour transfert/paiement uniquement) -------------
        idx_dest = rng.integers(0, n_comptes, size=n)
        destinataires = comptes_df["id_compte"].values[idx_dest]
        a_destinataire = np.isin(types_, ["transfert", "paiement"])
        destinataires = np.where(a_destinataire, destinataires, "")

        if not est_fraude:
            montants = _tirer_montant_normal(rng, n)
            heures = _tirer_heure_normale(rng, n)
            # appareil habituel (le premier de la liste du client, le plus souvent)
            appareils_choisis = []
            for id_cli in ids_client_emetteur:
                devs = appareils_par_client.get(id_cli, ["dev_000000"])
                appareils_choisis.append(devs[0])
            nouvel_appareil = np.zeros(n, dtype=bool)
            nouveau_destinataire = rng.random(n) < 0.15  # signal faible, arrive aussi normalement
        else:
            # scénario combiné : montant inhabituel + (appareil OU destinataire nouveau,
            # variabilité : parfois les deux) — jamais un signal totalement isolé
            montants = _tirer_montant_normal(rng, n) * rng.uniform(8, 35, size=n)
            montants = np.clip(montants, 100, 2_000_000).round(0)
            heures_a = _tirer_heure_normale(rng, n)
            heures_b = rng.integers(1, 5, size=n)
            mask_heure_atypique = rng.random(n) < 0.5
            heures = np.where(mask_heure_atypique, heures_b, heures_a)

            appareils_choisis = []
            nouvel_appareil = np.zeros(n, dtype=bool)
            for i, id_cli in enumerate(ids_client_emetteur):
                devs = appareils_par_client.get(id_cli, ["dev_000000"])
                # utilise l'appareil le + récent (souvent = "nouveau") 60% du temps
                if len(devs) > 1 and rng.random() < 0.6:
                    appareils_choisis.append(devs[-1])
                    nouvel_appareil[i] = True
                else:
                    appareils_choisis.append(devs[0])
            # nouveau destinataire : très fréquent en cas de fraude (signal fort)
            nouveau_destinataire = rng.random(n) < 0.8

        horodatages = [
            (AUJOURD_HUI - timedelta(days=int(j))).replace(
                hour=int(h), minute=int(rng.integers(0, 60)), second=int(rng.integers(0, 60))
            )
            for j, h in zip(jours_offset, heures)
        ]

        return pd.DataFrame({
            "id_compte_emetteur": ids_compte_emetteur,
            "id_compte_destinataire": destinataires,
            "montant": montants,
            "horodatage": [h.strftime("%Y-%m-%dT%H:%M:%S") for h in horodatages],
            "type": types_,
            "canal": canaux,
            "zone_geo": zones,
            "id_appareil": appareils_choisis,
            "nouvel_appareil": nouvel_appareil,
            "nouveau_destinataire": nouveau_destinataire,
            "fraude": est_fraude,
        })

    df_normales = _tirer_lot(n_normales, est_fraude=False)
    df_fraude = _tirer_lot(n_fraude, est_fraude=True)

    df = pd.concat([df_normales, df_fraude], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    df.insert(0, "id_transaction", [f"txn_{i:08d}" for i in range(1, len(df) + 1)])

    return df


def injecter_anomalies_qualite(df: pd.DataFrame, taux: float = TAUX_ANOMALIE_QUALITE,
                                seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Corrompt volontairement une partie des lignes pour donner une vraie
    matière au Sprint 2 (contrôle qualité) et à l'EDA. N'affecte jamais la
    colonne `fraude` (le label doit rester exploitable pour l'entraînement).
    """
    rng = np.random.default_rng(seed + 1)
    df = df.copy()
    n = len(df)
    n_par_type = int(n * taux / 7)  # 7 familles de problèmes réparties équitablement

    def _idx(n_choisi):
        return rng.choice(n, size=n_choisi, replace=False)

    # 1. Valeurs manquantes sur montant
    df.loc[_idx(n_par_type), "montant"] = np.nan

    # 2. Montant négatif (valeur impossible)
    idx = _idx(n_par_type)
    df.loc[idx, "montant"] = -df.loc[idx, "montant"].abs()

    # 3. Montant à zéro
    df.loc[_idx(n_par_type), "montant"] = 0

    # 4. Horodatage dans le futur (incohérent)
    idx = _idx(n_par_type)
    df.loc[idx, "horodatage"] = (AUJOURD_HUI + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

    # 5. Format de type incohérent (casse, espaces)
    idx = _idx(n_par_type)
    df.loc[idx, "type"] = df.loc[idx, "type"].str.upper() + "  "

    # 6. Canal manquant
    df.loc[_idx(n_par_type), "canal"] = np.nan

    # 7. Doublons exacts (lignes entièrement dupliquées, id_transaction inclus)
    idx = _idx(n_par_type)
    doublons = df.loc[idx].copy()
    df = pd.concat([df, doublons], ignore_index=True)

    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    comptes = pd.read_csv("../../data/synthetic/comptes.csv")
    appareils = pd.read_csv("../../data/synthetic/appareils.csv")

    df = generate_transactions(comptes, appareils)
    print(f"{len(df)} transactions générées (avant anomalies qualité)")
    print(f"Fraudes : {df['fraude'].sum()} ({df['fraude'].mean():.2%})")

    df_sale = injecter_anomalies_qualite(df)
    df_sale.to_csv("../../data/synthetic/transactions.csv", index=False)
    print(f"{len(df_sale)} lignes finales (avec anomalies qualité + doublons) "
          f"-> data/synthetic/transactions.csv")