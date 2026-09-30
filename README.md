# DataFlow360

**DataFlow360 prépare et explore des données de mobile money afin d'étudier deux risques financiers : la fraude sur les transactions et le défaut de remboursement des crédits.** Le projet génère des historiques synthétiques, en extrait des indicateurs de comportement et les exporte en CSV pour l'analyse et la préparation de futurs modèles.

Toutes les données sont fictives. Le projet ne prend pas de décisions financières : il n'entraîne ni ne sert encore de modèle de prédiction, et son dashboard utilise des exemples codés en dur.

## Voir le projet rapidement

L'API se lance avec Docker depuis la racine du dépôt. Docker Compose construit l'image et publie le port `8000`.

```bash
docker compose up --build api
```

Une fois le conteneur démarré :

- API : <http://localhost:8000>
- Vérification de santé : <http://localhost:8000/health>
- Documentation interactive : <http://localhost:8000/docs>

Arrêter le service avec `Ctrl+C`, puis, si nécessaire, supprimer les conteneurs avec `docker compose down`.

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

## Démarrer le dashboard

Le dashboard est indépendant du conteneur API et utilise des données codées en dur pour la démonstration. Il ne lit pas encore les résultats de l'API.

Prérequis : Python 3.10 ou supérieur. Installer ses dépendances dans l'environnement Python de votre choix :

```bash
python3 -m pip install dash plotly pandas
```

Depuis la racine du dépôt :

```bash
cd dashboard
python3 app.py
```

Ouvrir ensuite <http://127.0.0.1:8050>. Arrêter avec `Ctrl+C`.

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

## API

L'API est définie dans `api/main.py` et son image Docker dans `api/Dockerfile`. Les dépendances de l'API sont dans `requirements.txt` à la racine.

| Méthode | Route | Fonction actuelle |
| --- | --- | --- |
| `GET` | `/` | Message de bienvenue |
| `GET` | `/health` | Indique que l'API répond |

Les fichiers de routes fraude et crédit sont présents, mais ne contiennent pas encore de logique métier. L'API ne calcule donc pas encore de score de fraude ou de crédit.

## Structure du dépôt

```text
api/                  API FastAPI et Dockerfile
dashboard/            Démonstration web Dash/Plotly
data/
  synthetic/          CSV synthétiques
  processed/          CSV préparés pour l'analyse
  pipelines/models/   Emplacements de prototypes de modèles
notebooks/            Analyses exploratoires
src/data/             Génération des données synthétiques
src/features/         Construction des variables et datasets
streaming/            Fichiers réservés au streaming, encore vides
docker-compose.yml    Démarrage du service API
requirements.txt      Dépendances de l'API
```

## État actuel et limites

- **Données :** données synthétiques destinées au prototypage, jamais des informations réelles de clients.
- **Dashboard :** démonstration visuelle à données fictives, non connectée à l'API.
- **API :** seule la route d'accueil et la route `/health` sont actives.
- **Machine learning :** les scripts de modèles sont des exemples incomplets ou commentés ; aucune prédiction n'est servie.
- **Streaming :** les fichiers présents ne mettent pas encore en place de flux Kafka opérationnel.
- **Configuration :** aucun fichier `.env` n'est nécessaire pour lancer l'API actuelle.

Le projet est donc une base de démonstration et de développement, pas encore un système de décision financière prêt pour la production.
