"""
src/data/run_generation.py
 
Point d'entrée unique. Respecte l'ordre de dépendances entre les 8 tables :
clients -> comptes -> appareils -> activites -> transactions
-> historique_etat_compte -> credits -> remboursements
 
Usage :
    cd src/data
    python run_generation.py
"""
 
import os
import sys
import time
 
from generate_clients import generate_clients
from generate_comptes import generate_comptes
from generate_appareils import generate_appareils
from generate_activites import generate_activites
from generate_transactions import generate_transactions, injecter_anomalies_qualite
from generate_historique_etat_compte import generate_historique_etat_compte
from generate_credits import generate_credits
from generate_remboursements import generate_remboursements
 
OUT = "../../data/synthetic"
 
 
def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
 
    print("1/8 — clients...")
    clients = generate_clients(n_clients=6000)
    clients.to_csv(f"{OUT}/clients.csv", index=False)
    print(f"    {len(clients)} lignes")
 
    print("2/8 — comptes...")
    comptes = generate_comptes(clients)
    comptes.to_csv(f"{OUT}/comptes.csv", index=False)
    print(f"    {len(comptes)} lignes, "
          f"{(comptes['anciennete_jours'] < 90).sum()} comptes < 90j (cold start)")
 
    print("3/8 — appareils...")
    appareils = generate_appareils(clients)
    appareils.to_csv(f"{OUT}/appareils.csv", index=False)
    print(f"    {len(appareils)} lignes")
 
    print("4/8 — activites...")
    activites = generate_activites(clients, appareils)
    activites.to_csv(f"{OUT}/activites.csv", index=False)
    print(f"    {len(activites)} lignes")
 
    print("5/8 — transactions (peut prendre 1-2 minutes pour 500k lignes)...")
    transactions = generate_transactions(comptes, appareils, n_transactions=500_000)
    print(f"    {len(transactions)} lignes, {transactions['fraude'].sum()} fraudes "
          f"({transactions['fraude'].mean():.2%})")
    transactions_sale = injecter_anomalies_qualite(transactions)
    transactions_sale.to_csv(f"{OUT}/transactions.csv", index=False)
    print(f"    {len(transactions_sale)} lignes finales (avec anomalies qualité)")
 
    print("6/8 — historique_etat_compte...")
    historique = generate_historique_etat_compte(comptes, transactions_sale)
    historique.to_csv(f"{OUT}/historique_etat_compte.csv", index=False)
    print(f"    {len(historique)} lignes")
 
    print("7/8 — credits...")
    credits = generate_credits(comptes)
    credits.to_csv(f"{OUT}/credits.csv", index=False)
    print(f"    {len(credits)} lignes")
 
    print("8/8 — remboursements...")
    remboursements = generate_remboursements(credits, comptes, transactions_sale)
    remboursements.to_csv(f"{OUT}/remboursements.csv", index=False)
    print(f"    {len(remboursements)} lignes, taux de défaut : {remboursements['defaut'].mean():.1%}")
 
    print(f"\nTerminé en {time.time() - t0:.1f}s. 8 fichiers prêts dans {OUT}/")
    print("Prochaine étape : cd ../features && python build_dataset_fraude.py "
          "&& python build_dataset_credit.py")
 
 
if __name__ == "__main__":
    main()