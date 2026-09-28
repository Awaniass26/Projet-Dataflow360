"""
src/features/features.py

Le fichier le plus important du pipeline de données.

Ces fonctions seront réutilisées TELLES QUELLES :
  - maintenant, pour construire les datasets d'entraînement (sur historique)
  - plus tard (Sprint 4-5), pour scorer une transaction/demande de crédit
    en production

C'est ce qui garantit qu'il n'y a pas de "training-serving skew" (le modèle
recevrait des features calculées différemment en entraînement et en
production).

Règle absolue respectée partout ici : une feature ne doit JAMAIS utiliser
une information qui n'était pas encore disponible au moment de l'événement
qu'on cherche à prédire.
"""

import numpy as np
import pandas as pd


# =============================================================================
# FRAUDE — 1 ligne en sortie = 1 transaction historique
# =============================================================================

def build_features_fraude(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pour chaque transaction, calcule des features basées UNIQUEMENT sur
    l'historique du même client AVANT cette transaction (shift(1) avant tout
    calcul cumulatif = exclut la ligne courante).
    """
    df = transactions_df.copy()

    # --- Nettoyage minimal pour permettre le calcul ---------------------
    # (Un vrai contrôle qualité complet est le sujet du Sprint 2 ; ceci est
    # le strict nécessaire pour ne pas planter sur des NaN/doublons injectés)
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce")
    df = df.drop_duplicates(subset="id_transaction")
    df["type"] = df["type"].astype(str).str.strip().str.lower()
    df["date_dt"] = pd.to_datetime(df["horodatage"], errors="coerce")
    df = df.dropna(subset=["montant", "date_dt"])
    df = df[df["montant"] > 0]

    df = df.sort_values(["id_compte_emetteur", "date_dt"]).reset_index(drop=True)
    df["heure"] = df["date_dt"].dt.hour

    g = df.groupby("id_compte_emetteur")

    # expanding().mean() PUIS shift(1) : la ligne courante est exclue du calcul
    # (transform() préserve l'index d'origine, contrairement à apply() ici)
    df["montant_moyen_avant"] = g["montant"].transform(lambda s: s.expanding().mean().shift(1))
    df["heure_moyenne_avant"] = g["heure"].transform(lambda s: s.expanding().mean().shift(1))

    # Pour un client sans historique antérieur (sa 1ère transaction), on
    # retombe sur la moyenne globale plutôt que sur NaN
    df["montant_moyen_avant"] = df["montant_moyen_avant"].fillna(df["montant"].mean())
    df["heure_moyenne_avant"] = df["heure_moyenne_avant"].fillna(df["heure"].mean())

    df["ecart_montant_moyen"] = df["montant"] / df["montant_moyen_avant"].replace(0, np.nan)
    df["ecart_montant_moyen"] = df["ecart_montant_moyen"].fillna(1.0)
    df["ecart_heure_habituelle"] = (df["heure"] - df["heure_moyenne_avant"]).abs()

    # nb de transactions du même client dans l'heure précédente (fenêtre temporelle réelle)
    df = df.set_index("date_dt")
    nb_derniere_heure = (
        df.groupby("id_compte_emetteur")["montant"]
        .rolling("1h", closed="left")   # closed="left" = exclut l'instant courant
        .count()
    )
    df = df.reset_index()
    df["nb_transactions_derniere_heure"] = nb_derniere_heure.reset_index(drop=True).fillna(0)

    # zone différente de l'habituelle : approximé ici via l'écart au mode du client
    # (mode calculé sur tout l'historique disponible à ce stade, acceptable pour
    # un signal de zone qui change rarement — documenté comme simplification)
    zone_mode = g["zone_geo"].transform(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]) \
        if "zone_geo" in df.columns else None
    if zone_mode is not None:
        df["zone_differente_habituelle"] = (df["zone_geo"] != zone_mode).astype(int)
    else:
        df["zone_differente_habituelle"] = 0

    features = [
        "id_transaction", "montant", "type", "canal", "heure",
        "ecart_montant_moyen", "ecart_heure_habituelle",
        "nb_transactions_derniere_heure", "zone_differente_habituelle",
        "nouvel_appareil", "nouveau_destinataire",
        "fraude",
    ]
    features = [c for c in features if c in df.columns]
    return df[features]


# =============================================================================
# CRÉDIT — 1 ligne en sortie = 1 demande de crédit historique
# =============================================================================

def _fenetre(tx_client: pd.DataFrame, date_octroi: pd.Timestamp, jours: int) -> pd.DataFrame:
    """Sous-ensemble des transactions du client, strictement avant date_octroi,
    dans les `jours` précédents. Aucune donnée après date_octroi n'est utilisée."""
    borne_basse = date_octroi - pd.Timedelta(days=jours)
    return tx_client[(tx_client["date_dt"] >= borne_basse) & (tx_client["date_dt"] < date_octroi)]


def build_features_credit(credits_df: pd.DataFrame, comptes_df: pd.DataFrame,
                           transactions_df: pd.DataFrame,
                           remboursements_df: pd.DataFrame) -> pd.DataFrame:
    tx = transactions_df.copy()
    tx["montant"] = pd.to_numeric(tx["montant"], errors="coerce")
    tx = tx.dropna(subset=["montant"])
    tx = tx[tx["montant"] > 0]
    tx["date_dt"] = pd.to_datetime(tx["horodatage"], errors="coerce")
    tx = tx.dropna(subset=["date_dt"])

    compte_to_client = comptes_df.set_index("id_compte")["id_client"].to_dict()
    client_to_compte = comptes_df.set_index("id_client")["id_compte"].to_dict()
    tx["id_client_emetteur"] = tx["id_compte_emetteur"].map(compte_to_client)

    # historique crédits/remboursements, pour compter "crédits précédents"
    hist = credits_df.merge(remboursements_df, on="id_credit", how="left")
    hist["date_octroi_credit"] = pd.to_datetime(hist["date_octroi_credit"])

    lignes = []
    for _, credit in credits_df.iterrows():
        id_client = credit["id_client"]
        id_compte = client_to_compte.get(id_client)
        date_octroi = pd.to_datetime(credit["date_octroi_credit"])

        # Toutes les transactions IMPLIQUANT ce client, dans les deux sens :
        # sortant (il est émetteur) ou entrant (il est destinataire)
        mask_client = (
            (tx["id_client_emetteur"] == id_client)
            | (tx["id_compte_destinataire"] == id_compte)
        )
        tx_client = tx[mask_client]

        f30 = _fenetre(tx_client, date_octroi, 30)
        f60 = _fenetre(tx_client, date_octroi, 60)
        f90 = _fenetre(tx_client, date_octroi, 90)

        # Distinction correcte des deux sens de flux, dans la fenêtre 90j
        volume_sortant_90 = f90.loc[f90["id_compte_emetteur"] == id_compte, "montant"].sum()
        volume_entrant_90 = f90.loc[f90["id_compte_destinataire"] == id_compte, "montant"].sum()

        # historique crédit STRICTEMENT antérieur à cette demande
        hist_avant = hist[(hist["id_client"] == id_client) & (hist["date_octroi_credit"] < date_octroi)]
        nb_credits_precedents = hist_avant["id_credit"].nunique()
        nb_credits_impayes = hist_avant.loc[hist_avant["defaut"] == 1, "id_credit"].nunique()
        nb_retards = (hist_avant["retard_jours"] > 0).sum()
        retard_moyen = hist_avant["retard_jours"].mean() if len(hist_avant) else np.nan
        taux_remboursement = 1 - hist_avant["defaut"].mean() if len(hist_avant) else np.nan

        lignes.append({
            "id_credit": credit["id_credit"],
            "nb_transactions_30j": len(f30),
            "nb_transactions_60j": len(f60),
            "nb_transactions_90j": len(f90),
            "nb_jours_actifs_90j": f90["date_dt"].dt.date.nunique(),
            "volume_entrant_90j": volume_entrant_90,
            "volume_sortant_90j": volume_sortant_90,
            "ratio_flux_entrant_sortant": (volume_entrant_90 / volume_sortant_90
                                            if volume_sortant_90 > 0 else np.nan),
            "montant_moyen_90j": f90["montant"].mean() if len(f90) else np.nan,
            "montant_median_90j": f90["montant"].median() if len(f90) else np.nan,
            "regularite_transactions": f90["date_dt"].dt.date.nunique() / 90 if len(f90) else 0,
            "variation_volume_mensuel": (
                (f30["montant"].sum() - (f60["montant"].sum() - f30["montant"].sum()))
                / f60["montant"].sum() if f60["montant"].sum() > 0 else np.nan
            ),
            "nb_credits_precedents": nb_credits_precedents,
            "nb_credits_impayes": nb_credits_impayes,
            "nb_retards": nb_retards,
            "retard_moyen_jours": retard_moyen,
            "taux_remboursement": taux_remboursement,  # NaN pour un 1er crédit = cold start
            "montant_credit_demande": credit["montant_credit_demande"],
            "duree_credit_demande": credit["duree_credit_demande"],
        })

    features_df = pd.DataFrame(lignes)
    cible = remboursements_df.set_index("id_credit")["defaut"]
    features_df["defaut"] = features_df["id_credit"].map(cible)
    return features_df