"""
src/data/load_all.py

Charge les tables générées dans PostgreSQL et MongoDB.
Redis n'est volontairement pas inclus : il stockera les profils
comportementaux précalculés (Sprint 4), pas les données brutes générées.

Prérequis : docker-compose up -d
Usage     : python load_all.py
"""

import subprocess
import sys

if __name__ == "__main__":
    print("=== Chargement PostgreSQL (clients, comptes, credits, remboursements, transactions) ===")
    subprocess.run([sys.executable, "load_postgres.py"], check=True)

    print("\n=== Chargement MongoDB (appareils, activites, historique_etat_compte) ===")
    subprocess.run([sys.executable, "load_mongodb.py"], check=True)

    print("\nTerminé. Les 8 tables sont réparties sur 2 bases (PostgreSQL + MongoDB).")