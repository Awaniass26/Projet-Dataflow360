# DataFlow360

**DataFlow360** est un projet académique consacré à l'analyse des risques liés au **mobile money au Sénégal** : détection de fraude sur les transactions et scoring du risque de défaut sur les demandes de crédit.

La plateforme développée s'appelle **SenTerangaSafe**. Elle repose sur une API FastAPI, un frontend React, un pipeline temps réel avec Kafka, des modèles de Machine Learning avec scikit-learn et une base de données PostgreSQL.

> ⚖️ **Principe métier :** les scores produits par la plateforme sont des **aides à la décision**. Ils ne constituent ni une preuve juridique de fraude, ni une décision automatique d'octroi ou de refus de crédit. Les décisions finales restent humaines.

> 🧪 **Données :** toutes les données utilisées dans le projet sont synthétiques et ne représentent pas de vrais clients.

---

## 1. Voir le projet rapidement

Depuis la racine du dépôt :

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps -a
```

Docker Compose démarre la stack du projet : API FastAPI, PostgreSQL, MongoDB, Redis, Kafka, producteur et consommateur de transactions, frontend React et services associés.

Le service d'initialisation `db-init` prépare le schéma de la base et crée les comptes initiaux.

### Accès aux services

| Service                   | URL / Adresse                |
| ------------------------- | ---------------------------- |
| API FastAPI               | http://localhost:8000        |
| Documentation Swagger     | http://localhost:8000/docs   |
| Vérification de santé     | http://localhost:8000/health |
| Frontend React            | http://localhost:3000        |
| MLflow (profil optionnel) | http://localhost:5000        |
| PostgreSQL                | `localhost:5433`             |
| MongoDB                   | `localhost:27018`            |
| Redis                     | `localhost:6379`             |
| Kafka                     | `localhost:9092`             |

### Arrêter la stack

```bash
docker compose down
```

Pour supprimer également les volumes persistants :

```bash
docker compose down -v
```

**Attention :** cette dernière commande supprime les données persistées dans les volumes, notamment les données des bases de données. À utiliser uniquement pour repartir de zéro.

### Profils optionnels

Lancer MLflow :

```bash
docker compose --profile mlflow up -d
```

Exécuter les tests automatisés :

```bash
docker compose --profile test run --rm api-tests
```

### Comptes de démonstration

Les comptes sont créés par `api/scripts/seed_users.py`.

| Email                              | Mot de passe            | Rôle      |
| ---------------------------------- | ----------------------- | --------- |
| `admin@dataflow360.com`            | `admin1234`             | `admin`   |
| `service-consumer@dataflow360.com` | `service-consumer-2026` | `analyst` |

> 🔐 Ces identifiants sont destinés à un environnement local de démonstration. Ils doivent être modifiés avant tout déploiement non local.

---

## 2. Ce que le projet analyse

### 2.1. Détection du risque de fraude

Pour chaque transaction mobile money synthétique, le pipeline prépare des indicateurs comportementaux, notamment :

* l'écart du montant de la transaction par rapport aux habitudes du compte ;
* la détection d'une heure inhabituelle ;
* l'apparition d'un nouvel appareil ou d'un nouveau destinataire ;
* les écarts temporels et les montants par rapport au profil du client ;
* le type et le canal de la transaction.

Le modèle de fraude utilise **8 features** et produit un score de risque ainsi qu'un niveau de risque : `low`, `medium` ou `high`.

Les alertes classées `high` sont enregistrées en base de données pour permettre leur traitement par un analyste.

### 2.2. Scoring du risque de crédit

Pour chaque demande de crédit, le pipeline résume l'activité financière antérieure du client.

Les variables exploitées comprennent :

* l'âge et l'ancienneté du compte ;
* le nombre et le volume des transactions sur 90 jours ;
* les flux financiers entrants et sortants ;
* le solde moyen ;
* la régularité des revenus et la stabilité des flux ;
* l'historique des crédits précédents ;
* les retards et les impayés ;
* le montant et la durée du crédit demandé ;
* le type d'activité.

Le modèle de crédit utilise **15 features** et produit un score de risque ainsi qu'un statut d'éligibilité.

Le seuil métier documenté est de `0.90`. Il doit être validé par l'équipe Data Science avant toute interprétation métier définitive.

### 2.3. Deux modes de scoring du crédit

| Route                     | Données fournies                              | Traitement                                                                                     |
| ------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `POST /credit/score`      | Les 15 features saisies manuellement          | Évalue directement les données fournies. Cette route permet notamment de tester le contrat ML. |
| `POST /credit/score/auto` | 4 champs : client, montant, durée et activité | Calcule les 12 autres features à partir de l'historique du client.                             |

Ces deux modes permettent de tester le modèle directement ou de calculer un score à partir des données disponibles pour un client.

---

## 3. Architecture du projet

```text
┌──────────────────────┐    HTTP/JSON + JWT     ┌──────────────────────┐
│  Frontend React/Vite │ ─────────────────────► │     API FastAPI      │
│      Port 3000       │ ◄───────────────────── │      Port 8000       │
└──────────────────────┘                        └──────────┬───────────┘
                                                           │
                     ┌─────────────────────────────────────┼────────────────────────┐
                     ▼                                     ▼                        ▼
          ┌────────────────────┐              ┌────────────────────┐   ┌──────────────────┐
          │  Services métier   │              │    Repositories    │   │   Modèles ML     │
          │   Fraude / Crédit  │              │     SQLAlchemy     │   │  Pipelines .pkl  │
          └────────────────────┘              └─────────┬──────────┘   └──────────────────┘
                                                        ▼
                                             ┌────────────────────┐
                                             │    PostgreSQL      │
                                             │     Tables api_*   │
                                             └────────────────────┘


Pipeline temps réel :

Transaction Producer
        │
        ▼
Kafka : transactions.raw
        │
        ▼
Fraud Consumer
        │
        ▼
API FastAPI + modèle de fraude
        │
        ▼
Persistance des alertes HIGH
```

### Rôle des composants

| Composant               | Rôle                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| **Frontend React/Vite** | Interface destinée aux analystes : clients, alertes, scoring et indicateurs clés.                      |
| **API FastAPI**         | Validation des données, authentification JWT, orchestration métier et réponses JSON.                   |
| **Services métier**     | Contiennent la logique de détection de fraude et de scoring de crédit, indépendamment des routes HTTP. |
| **Repositories**        | Gèrent l'accès à PostgreSQL à travers SQLAlchemy.                                                      |
| **Modèles ML**          | Pipelines scikit-learn sérialisés en `.pkl`, chargés à la demande avec un cache LRU.                   |
| **PostgreSQL**          | Stocke les utilisateurs, clients, transactions, alertes, demandes et scores.                           |
| **MongoDB**             | Est prévu pour les profils comportementaux et le feature store.                                        |
| **Redis**               | Est prévu pour le cache et les compteurs temps réel.                                                   |
| **Kafka**               | Transporte les événements entre le producteur et le consommateur de transactions.                      |
| **MLflow**              | Permet le suivi des expériences de Machine Learning via un profil optionnel.                           |

### Séparation des responsabilités

Le backend suit une architecture en couches :

```text
Router → Service → Repository → Database
```

* Le **Router** expose les routes HTTP et valide les entrées.
* Le **Service** applique les règles métier et appelle le modèle ML.
* Le **Repository** gère les opérations de persistance.
* La **Database** conserve les données.

Le modèle ML est invoqué depuis le service métier, et non directement depuis la route HTTP.

---

## 4. Structure du dépôt

```text
Projet-Dataflow360/
│
├── api/                         # Backend FastAPI
│   ├── core/                    # Configuration, sécurité, erreurs
│   ├── db/                      # Modèles SQLAlchemy, sessions, migrations
│   ├── repositories/             # Accès aux données
│   ├── routers/                 # Routes HTTP
│   ├── schemas/                 # Schémas Pydantic
│   ├── scripts/                 # Initialisation, génération, utilisateurs
│   └── services/                # Logique métier et intégration ML
│
├── frontend/                    # Frontend React / TypeScript / Vite
│   └── src/
│       ├── features/             # Auth, dashboard, clients, fraude, scoring
│       └── services/             # Client HTTP vers l'API
│
├── data/
│   ├── synthetic/                # Données synthétiques
│   └── processed/                # Datasets préparés
│
├── eda/
│   └── notebooks/                # Analyses exploratoires
│
├── models/
│   ├── credit/                   # Modèle de scoring crédit et artefacts
│   └── fraude/                   # Modèle de fraude et artefacts
│
├── src/
│   ├── data/                     # Génération des données synthétiques
│   └── features/                 # Construction des variables et datasets
│
├── streaming/                    # Producteur et consommateur Kafka
├── tests/                        # Tests automatisés
├── docker-compose.yml            # Stack de développement
├── requirements.txt              # Dépendances Python
├── .env.example                  # Exemple de configuration
└── README.md                     # Documentation principale
```

---

## 5. Documentation détaillée

| Document                                   | Contenu                                                                                      |
| ------------------------------------------ | -------------------------------------------------------------------------------------------- |
| [`api/README.md`](api/README.md)           | Backend : endpoints, authentification JWT, scoring, fraude, Kafka, base de données et tests. |
| [`frontend/README.md`](frontend/README.md) | Frontend : structure React, scripts Vite, communication avec l'API et débogage.              |
| [`eda/README.md`](eda/README.md)           | Analyse exploratoire : notebooks, méthodologie et dépendances.                               |
| `docs/architecture.md`                     | Documentation détaillée de l'architecture, à compléter.                                      |
| `docs/troubleshooting.md`                  | Erreurs courantes et solutions, à compléter.                                                 |

---

## 6. Installation et démarrage détaillés

### 6.1. Prérequis

Avant de commencer, installer :

* Git ;
* Docker version 24 ou supérieure ;
* Docker Compose v2, avec la commande `docker compose`.

### 6.2. Première installation

```bash
git clone <url-du-repo>
cd Projet-Dataflow360

cp .env.example .env
```

Ouvrir ensuite le fichier `.env` et vérifier les valeurs de configuration.

Démarrer les services :

```bash
docker compose up -d --build
docker compose ps -a
```

Un service `dataflow360-db-init` peut apparaître avec l'état `Exited (0)` après son exécution. C'est normal pour un service d'initialisation ponctuel.

Pour consulter ses logs :

```bash
docker compose logs db-init
```

### 6.3. Démarrages suivants

Une fois la stack construite :

```bash
docker compose up -d
```

### 6.4. Vérifications

Vérifier que l'API répond :

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Lister les routes exposées par l'API :

```bash
curl -fsS http://127.0.0.1:8000/openapi.json \
  | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['paths'].keys()))"
```

Consulter les logs de l'API :

```bash
docker compose logs --tail=100 api
```

Consulter les logs du consommateur de fraude :

```bash
docker compose logs --tail=100 fraud-consumer
```

---

## 7. Génération et préparation des données

### 7.1. Datasets destinés au Machine Learning

Les datasets d'entraînement principaux sont :

* `data/processed/dataset_credit.csv` ;
* `data/processed/dataset_fraude.csv`.

Le volume documenté est de **2 000 000 de lignes**. Les datasets sont associés aux analyses exploratoires et à la préparation des variables.

Un fichier `.dvc` est utilisé pour le versionnement des données concernées.

### 7.2. Données PostgreSQL de démonstration

Les tables de l'API sont créées par Docker Compose. Pour générer les données de démonstration, exécuter explicitement :

```bash
docker compose exec api python -m api.scripts.generate
```

Le générateur est déterministe et utilise la seed `RANDOM_SEED=42`.

Les volumes documentés sont :

| Table                     | Volume approximatif |
| ------------------------- | ------------------: |
| `api_clients`             |         500 clients |
| `api_transactions`        | 23 750 transactions |
| `api_fraud_alerts`        |       1 900 alertes |
| `api_credit_applications` |        750 demandes |
| `api_credit_scores`       |          750 scores |

> ⚠️ **Attention :** le générateur vide les tables concernées avant de les remplir. Cette opération remplace donc leur contenu existant. Vérifier les données avant de l'exécuter.

Les volumes du générateur diffèrent du guide initial de l'équipe, qui indiquait environ 10 000 transactions et 800 alertes. Les valeurs présentées ici correspondent aux volumes documentés pour le générateur actuel.

### 7.3. Régénération des CSV synthétiques

Installer les dépendances nécessaires :

```bash
python3 -m pip install numpy pandas faker
```

Générer les données :

```bash
cd src/data
python3 run_generation.py

cd ../features
python3 build_dataset_fraude.py
python3 build_dataset_credit.py

cd ../..
```

---

## 8. État actuel du projet

### Fonctionnalités documentées comme opérationnelles

* API FastAPI avec les routes `/`, `/health`, `/auth/*`, `/clients/*`, `/fraud/*` et `/credit/*`.
* Authentification JWT avec flux OAuth2 password et algorithme HS256.
* Modèle de fraude intégré avec 8 features, défini dans `api/services/ml_contracts.py`.
* Modèle de crédit intégré avec 15 features et deux modes d'appel.
* Pipeline Kafka documenté de bout en bout : producteur → consommateur → API → persistance.
* Frontend React connecté à l'API réelle, sans dépendre des mocks pour les fonctionnalités concernées.
* Stack Docker documentée avec 11 services et des healthchecks.

### Points à valider ou à corriger

| Point                                              | État documenté                                                                      |
| -------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Seuil d'éligibilité crédit `0.90`                  | À valider avec l'équipe Data Science.                                               |
| Échelle de `taux_remboursement` (`0.5` ou `0–100`) | Bug signalé dans `compute_features_from_history`.                                   |
| Rôle `viewer` mentionné dans le guide              | Non implémenté selon la documentation ; seuls `admin` et `analyst` sont documentés. |
| `explanation_factors` et SHAP                      | Valeur `null` observée ; intégration non active.                                    |
| Code mort dans `compute_features_from_history`     | `return` dupliqué à nettoyer.                                                       |
| `logging.warning` sur les features                 | À passer en `debug` si ces logs sont uniquement destinés au débogage.               |
| Volumes des données de démonstration               | Écart avec le guide initial, documenté ci-dessus.                                   |

Les résultats de tests, les métriques de performance ML et les validations fonctionnelles doivent être vérifiés à partir des sorties réelles avant d'être annoncés comme acquis.

---

## 9. Ce que le projet n'est pas

DataFlow360 / SenTerangaSafe est une base de démonstration et de développement pour un projet académique.

Ce n'est pas :

* un système de production prêt pour le secteur financier ;
* un système qui bloque ou autorise automatiquement une transaction ;
* un système qui accorde ou refuse automatiquement un crédit ;
* un système entraîné sur des données de clients réels.

Les modèles et leurs résultats doivent être évalués, documentés et validés avant toute utilisation dans un contexte réel.

---

## 10. Cadre éthique et juridique

Le fonctionnement attendu suit ce principe :

```text
Données
   │
   ▼
Analyse et préparation des variables
   │
   ▼
Modèle de Machine Learning
   │
   ▼
Score de risque
   │
   ▼
Information et explication destinées à l'analyste
   │
   ▼
Décision humaine
```

Le système ne doit pas :

* bloquer automatiquement une transaction ;
* accuser juridiquement un client sur la seule base d'un score ;
* accorder automatiquement un crédit ;
* refuser automatiquement un crédit.

**Les scores constituent des aides à la décision. Les décisions finales restent humaines.**

---

## 11. Contribuer au projet

### 11.1. Modifier une fonctionnalité

Lorsqu'une fonctionnalité du backend est modifiée, vérifier les éléments concernés dans cet ordre :

1. Le schéma Pydantic dans `api/schemas/`.
2. Le service métier dans `api/services/`.
3. Le repository dans `api/repositories/`.
4. La route HTTP dans `api/routers/`.
5. Les tests dans `tests/`.
6. La documentation Swagger : docstrings et `responses=ERROR_RESPONSES`.
7. Les logs et la gestion des erreurs.
8. Le README concerné : racine, backend ou frontend.

Toutes les couches ne doivent pas nécessairement être modifiées pour chaque évolution ; seules celles concernées par le changement doivent l'être.

### 11.2. Conventions de développement

* **Code :** anglais.
* **Commentaires et docstrings :** français.
* **Commits :** conventions telles que `feat:`, `fix:`, `docs:` et `chore:`.
* **Branches :** `feat/<nom>` et `fix/<nom>`.

### 11.3. Vérifications avant une Pull Request

Avant de proposer une modification :

```bash
git status
git diff
```

Exécuter ensuite les tests adaptés au changement, vérifier le fonctionnement de la fonctionnalité et mettre à jour la documentation si nécessaire.

---

*Dernière mise à jour : octobre 2026.*

Pour toute modification d'une route, d'un schéma, d'une configuration ou d'un test, mettre à jour la documentation concernée afin de conserver un README cohérent avec le code.
