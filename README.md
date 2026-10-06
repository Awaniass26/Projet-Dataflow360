# DataFlow360

**DataFlow360 prépare et explore des données de mobile money afin d'étudier deux risques financiers : la fraude sur les transactions et le défaut de remboursement des crédits.** Le projet génère des historiques synthétiques, en extrait des indicateurs de comportement et les exporte en CSV pour l'analyse et la préparation de futurs modèles.


Toutes les données de démonstration sont synthétiques. Le backend expose des routes de prédiction, mais répond en mode simulation tant qu'aucun modèle réel n'est configuré. Le frontend React utilise encore des données mockées. Aucun résultat ne constitue une décision financière.

# Projet-Dataflow360

> Plateforme intelligente de détection de fraude et d'évaluation du risque de crédit dans les services de mobile money au Sénégal.


## Voir le projet rapidement

Depuis la racine du dépôt, démarrer l'ensemble des services :

```bash
docker compose up --build -d
```

Compose démarre l'API FastAPI, PostgreSQL, MongoDB et Redis. Il crée le schéma PostgreSQL avant le démarrage de l'API ; il ne génère pas automatiquement de lignes.

- API : <http://localhost:8000>
- Vérification de santé : <http://localhost:8000/health>
- Documentation interactive : <http://localhost:8000/docs>
- PostgreSQL depuis l'hôte : `localhost:5433` (port interne Docker : `5432`)

Arrêter les services sans supprimer les volumes de données :

```bash
docker compose down
```

`docker compose down -v` supprime également les volumes et donc les données des bases.

Pour exécuter les tests API dans Docker :

```bash
docker compose --profile test run --rm api-tests
```

## Ce que le projet analyse

**Risque de fraude par transaction.** Pour chaque transaction synthétique, le pipeline prépare des indicateurs tels que l'écart du montant aux habitudes du compte, l'heure inhabituelle, le nombre de transactions de la dernière heure, un nouvel appareil ou destinataire, et un changement de zone géographique. Le dataset conserve également l'étiquette de fraude générée, afin de permettre une analyse supervisée ultérieure.

**Risque de crédit par demande.** Pour chaque demande de crédit, le pipeline résume l'activité financière antérieure du client : volumes et nombres de transactions sur 30, 60 et 90 jours, flux entrants et sortants, jours actifs, ainsi que l'historique des crédits, défauts et retards. Il conserve le montant et la durée demandés ainsi que l'étiquette de défaut générée.

Les scripts produisent des jeux de données analytiques ; ils ne calculent pas encore de score prédictif. L'API actuelle répond uniquement sur `/` et `/health`, et le dashboard illustre l'interface avec des données fictives sans lire les CSV ni appeler l'API.

Le flux de préparation des données est :

```text
Générateurs Python
    -> fichiers CSV dans data/synthetic/
    -> construction des variables dans src/features/
    -> jeux de données dans data/processed/
    -> exploration dans les notebooks
```

Les scripts de génération créent notamment 6 000 clients et 500 000 transactions synthétiques. La génération des transactions peut prendre une à deux minutes et remplace les CSV correspondants dans `data/synthetic/`.

## Démarrer le frontend

Le frontend est une application React/TypeScript servie en développement par Vite. Ses vues utilisent encore des données mockées et ne consomment pas encore les réponses de l'API.

Prérequis : Node.js 20 ou supérieur et npm.

```bash
cd frontend
npm install
npm run dev
```

Ouvrir <http://localhost:5173>. L'URL de l'API peut être configurée dans `frontend/.env` avec `VITE_API_BASE_URL`.

## Générer et préparer les données

Cette étape est optionnelle : les CSV synthétiques et les datasets préparés sont déjà présents dans le dépôt. Pour régénérer les données, Python 3.10 ou supérieur et les paquets `numpy`, `pandas` et `faker` sont nécessaires.

```bash
python3 -m pip install numpy pandas faker
```

Depuis la racine du dépôt, lancer les générateurs dans leur ordre prévu :

```bash
cd src/data
python3 run_generation.py
cd ../features
python3 build_dataset_fraude.py
python3 build_dataset_credit.py
```

Résultats attendus :

- `data/synthetic/` : les huit tables générées, dont `clients.csv`, `transactions.csv`, `credits.csv` et `remboursements.csv`.
- `data/processed/dataset_fraude.csv` : variables calculées pour les transactions.
- `data/processed/dataset_credit.csv` : variables calculées pour les demandes de crédit.

Pour revenir à la racine après ces commandes : `cd ../..`.

## Générer les données PostgreSQL de démonstration

Les tables API sont créées au démarrage de Compose, mais restent vides jusqu'à l'exécution explicite du générateur :

```bash
docker compose exec api python -m api.scripts.generate
```

Le dataset PostgreSQL est déterministe : chaque exécution produit les mêmes identifiants, valeurs et dates. Attention : le générateur vide les tables `clients`, `transactions`, `fraud_alerts`, `credit_applications` et `credit_scores` avant de les remplir. Ne l'exécuter que si vous souhaitez remplacer leur contenu.

## API

L'API est définie dans `api/main.py`, ses routes métier sont dans `api/routers/` et son image Docker dans `api/Dockerfile`. Les dépendances sont dans `requirements.txt` à la racine. Sans modèle configuré, les routes de prédiction renvoient une réponse de simulation si `SIMULATION_ENABLED=true`.

| Méthode | Route | Fonction actuelle |
| --- | --- | --- |
| `GET` | `/` | Message de bienvenue |
| `GET` | `/health` | Indique que l'API répond |
| `GET` | `/clients` | Liste les clients stockés dans PostgreSQL |
| `GET` | `/clients/{client_id}` | Détail d'un client et de son historique |
| `POST` | `/fraud/predict` | Évalue une transaction (modèle configuré ou simulation) |
| `GET` | `/fraud/alerts`, `/fraud/stats` | Consulte les alertes et indicateurs fraude |
| `POST` | `/credit/score` | Évalue une demande de crédit (modèle configuré ou simulation) |
| `GET` | `/credit/applications`, `/credit/stats` | Consulte les demandes et indicateurs crédit |

Les routes de consultation nécessitent PostgreSQL. Les routes de prédiction peuvent répondre en simulation ; les résultats simulés ne sont pas des décisions financières.

## Structure du dépôt

```text
api/                  API FastAPI, scripts de génération et Dockerfile
frontend/             Application React/TypeScript avec Vite
data/
  synthetic/          CSV synthétiques
  processed/          CSV préparés pour l'analyse
eda/notebooks/        Analyses exploratoires
models/fraude/        Scripts et artefacts liés aux modèles
src/data/             Génération des données synthétiques
src/features/         Construction des variables et datasets
streaming/            Producteur et consommateur de données
tests/                Tests de l'API et des repositories
docker-compose.yml    Services API et bases de données
requirements.txt      Dépendances Python
```

## État actuel et limites

- **Données :** données synthétiques destinées au prototypage, jamais des informations réelles de clients.
- **Frontend :** interface de démonstration dont les vues utilisent encore des mocks.
- **API :** routes clients, fraude et crédit disponibles ; les prédictions restent simulées tant que les modèles ne sont pas configurés.
- **Données PostgreSQL :** schéma initialisé par Compose ; le dataset de démonstration doit être généré explicitement.
- **Machine learning :** la disponibilité d'une route de prédiction ne signifie pas qu'un modèle réel est chargé.
- **Configuration :** les valeurs par défaut de Compose suffisent pour démarrer ; `.env` est facultatif et ne doit pas contenir de secrets committés.

Le projet est donc une base de démonstration et de développement, pas encore un système de décision financière prêt pour la production.
