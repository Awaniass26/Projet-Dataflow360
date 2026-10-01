"""
src/data/load_mongodb.py

Insère dans MongoDB les données semi-structurées / logs : appareils,
activites, historique_etat_compte.

Prérequis : docker-compose up -d   (au moins le service mongodb)
Usage     : python load_mongodb.py
"""

import os
import pandas as pd
from pymongo import MongoClient

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
except ImportError:
    pass

MONGO_USER = os.getenv("MONGO_USER", "terangasafe")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "terangasafe_pwd")
MONGO_DB = os.getenv("MONGO_DB", "terangasafe")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27018")  # 27018 chez toi

SYNTHETIC_DIR = "../../data/synthetic"
COLLECTIONS = ["appareils", "activites", "historique_etat_compte"]


def get_client():
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    return MongoClient(uri)


def load_collection(db, collection_name: str):
    path = f"{SYNTHETIC_DIR}/{collection_name}.csv"
    if not os.path.exists(path):
        print(f"  ⚠ {path} introuvable, ignoré (as-tu lancé run_generation.py ?)")
        return
    df = pd.read_csv(path)
    documents = df.to_dict(orient="records")

    collection = db[collection_name]
    collection.delete_many({})
    if documents:
        collection.insert_many(documents)
    print(f"  {collection_name} : {len(documents)} documents insérés")


if __name__ == "__main__":
    print(f"Connexion à MongoDB ({MONGO_HOST}:{MONGO_PORT}/{MONGO_DB})...")
    client = get_client()
    db = client[MONGO_DB]
    for coll in COLLECTIONS:
        load_collection(db, coll)
    print("Terminé. Collections MongoDB : " + ", ".join(COLLECTIONS))