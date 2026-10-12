# DataFlow360 — Backend

> **DataFlow360** est le nom du projet académique. **SenTerangaSafe** est le nom de la plateforme qui en découle.
>
> Le backend expose une API **FastAPI** dédiée à la gestion des clients, à la détection de fraude, au scoring de crédit et aux statistiques associées.

**Principe métier :** les scores produits par les modèles sont des aides à la décision. Ils ne constituent ni une preuve juridique de fraude ni une décision automatique d’octroi ou de refus de crédit. Les données utilisées dans le projet sont synthétiques.

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture](#2-architecture)
3. [Structure du projet](#3-structure-du-projet)
4. [Démarrage rapide](#4-démarrage-rapide)
5. [URLs locales](#5-urls-locales)
6. [Configuration](#6-configuration)
7. [Authentification JWT](#7-authentification-jwt)
8. [Endpoints de l'API](#8-endpoints-de-lapi)
9. [Scoring de crédit](#9-scoring-de-crédit)
10. [Détection de fraude](#10-détection-de-fraude)
11. [Pipeline Kafka temps réel](#11-pipeline-kafka-temps-réel)
12. [Base de données et données synthétiques](#12-base-de-données-et-données-synthétiques)
13. [Chargement des modèles ML](#13-chargement-des-modèles-ml)
14. [Tests et état des vérifications](#14-tests-et-état-des-vérifications)
15. [Intégration frontend](#15-intégration-frontend)
16. [Limites et prochaines étapes](#16-limites-et-prochaines-étapes)

---

## 1. Vue d'ensemble

DataFlow360 est un projet académique consacré à l'analyse des risques liés au **mobile money au Sénégal**.

Le projet combine :

* une API backend développée avec **FastAPI** ;
* une interface frontend développée avec **React/Vite** ;
* un modèle de machine learning pour la détection de fraude ;
* un modèle de machine learning pour le scoring de crédit ;
* un pipeline de traitement de transactions avec **Apache Kafka** ;
* **PostgreSQL** pour la persistance des données ;
* **SQLAlchemy** pour l'accès aux données ;
* **Redis** pour les besoins de cache prévus dans l'architecture ;
* **MongoDB** pour les profils comportementaux prévus dans l'architecture ;
* **MLflow** pour le suivi des expériences ML, selon la configuration du projet.

Le backend a notamment pour objectifs de :

* consulter les clients et leurs informations disponibles ;
* évaluer le risque associé à une transaction ;
* enregistrer et suivre les alertes de fraude ;
* calculer un score de crédit à partir des variables du modèle ;
* conserver l'historique des scores ;
* fournir des indicateurs utiles à l'analyse des risques.

Le projet est un démonstrateur académique. Les résultats obtenus sur les données synthétiques ne garantissent pas les mêmes performances sur des transactions réelles.

---

## 2. Architecture

### 2.1. Vue globale

```text
                  FRONTEND REACT / VITE
                           |
                           | HTTP / JSON + JWT
                           v
                    API FASTAPI
                           |
              +------------+-------------+
              |                          |
              v                          v
       Services métier             Repositories
       - Détection fraude          - SQLAlchemy
       - Scoring crédit                  |
              |                          v
              v                     PostgreSQL
          Modèles ML
          - Fraude
          - Crédit


              PIPELINE FRAUDE TEMPS RÉEL

       Transaction Producer
                |
                v
          Kafka topic
       "transactions.raw"
                |
                v
         Fraud Consumer
                |
                | POST /fraud/predict + JWT
                v
            API FastAPI
                |
                v
          Modèle de fraude
                |
                v
       Persistance des alertes
       selon les règles métier
```

### 2.2. Rôle des composants

| Composant           | Responsabilité                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Frontend React/Vite | Interface de consultation des clients, scores, alertes et indicateurs.                                             |
| API FastAPI         | Point d'entrée HTTP, validation des requêtes, authentification et réponses JSON.                                   |
| Services métier     | Application des règles métier et appel des modèles ML.                                                             |
| Repositories        | Accès aux données et opérations de persistance via SQLAlchemy.                                                     |
| Modèle de fraude    | Estimation du risque de fraude d'une transaction.                                                                  |
| Modèle de crédit    | Calcul du score de crédit à partir des variables attendues.                                                        |
| PostgreSQL          | Stockage des utilisateurs, clients, transactions, alertes et scores.                                               |
| Kafka               | Transport des messages de transactions entre le producer et le consumer.                                           |
| Redis et MongoDB    | Composants prévus dans l'architecture ; leur utilisation effective doit être vérifiée dans les services concernés. |
| MLflow              | Suivi des expériences ML lorsque le profil correspondant est activé.                                               |

### 2.3. Séparation des responsabilités

Le principe d'architecture est le suivant :

```text
Router → Service → Repository → Database
              |
              v
           Modèle ML
```

* Les **routers** exposent les routes HTTP.
* Les **services** contiennent la logique métier et appellent les modèles.
* Les **repositories** assurent l'accès aux données.
* Les **modèles ML** sont utilisés par les services concernés.

Cette séparation facilite les tests, la maintenance et l'évolution du backend.

---

## 3. Structure du projet

Les principaux répertoires et fichiers documentés sont organisés de la manière suivante :

```text
Projet-Dataflow360/
├── api/
│   ├── main.py
│   ├── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── error_handlers.py
│   │   ├── exceptions.py
│   │   └── security.py
│   ├── db/
│   │   ├── models.py
│   │   ├── migrations.py
│   │   └── session.py
│   ├── repositories/
│   │   ├── client_repository.py
│   │   ├── credit_repository.py
│   │   ├── fraud_repository.py
│   │   └── user_repository.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── client.py
│   │   ├── credit.py
│   │   └── fraud.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── client.py
│   │   ├── common.py
│   │   ├── credit.py
│   │   ├── fraud.py
│   │   └── health.py
│   ├── scripts/
│   │   ├── generate.py
│   │   ├── init_db.py
│   │   └── seed_users.py
│   └── services/
│       ├── credit_service.py
│       ├── fraud_service.py
│       ├── ml_contracts.py
│       └── model_loader.py
├── models/
│   ├── credit/
│   │   └── modele_scoring_credit_final.pkl
│   └── fraude/
│       └── modele_fraude_final.pkl
├── streaming/
│   ├── producer.py
│   ├── consumer.py
│   └── Dockerfile
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_credit.py
│   ├── test_fraud.py
│   ├── test_generator.py
│   ├── test_health.py
│   ├── test_init_db.py
│   └── test_repositories.py
├── frontend/
├── docker-compose.yml
├── .env.example
└── README.md
```

Cette arborescence présente les principaux fichiers documentés. Elle doit être adaptée si des fichiers ont été ajoutés, déplacés ou supprimés dans la version courante du dépôt.

---

## 4. Démarrage rapide

### 4.1. Prérequis

* Git
* Docker
* Docker Compose v2
* Un terminal
* Les fichiers du dépôt, notamment les modèles ML si les prédictions réelles sont souhaitées

### 4.2. Préparer l'environnement

Depuis la racine du projet :

```bash
cd ~/Projet-Dataflow360
```

Créer le fichier d'environnement s'il n'existe pas déjà :

```bash
cp .env.example .env
```

Si un fichier `.env` existe déjà, ne l'écrase pas sans avoir sauvegardé les valeurs locales.

Vérifier ensuite les variables nécessaires dans `.env`, en particulier celles relatives à PostgreSQL, à l'authentification, aux modèles ML et à Kafka.

### 4.3. Démarrer les services

```bash
docker compose up -d --build
```

Vérifier l'état des conteneurs :

```bash
docker compose ps -a
```

Un service d'initialisation comme `dataflow360-db-init` peut apparaître en état `Exited` après avoir terminé son travail. Il faut vérifier son code de sortie et ses logs pour savoir si l'initialisation s'est terminée correctement.

### 4.4. Consulter les logs

Logs de l'API :

```bash
docker compose logs --tail=100 api
```

Logs du consumer :

```bash
docker compose logs --tail=100 fraud-consumer
```

Logs du producer :

```bash
docker compose logs --tail=100 transaction-producer
```

Suivre les logs de l'API en direct :

```bash
docker compose logs -f api
```

### 4.5. Arrêter les services

```bash
docker compose down
```

> **Attention :** `docker compose down -v` supprime également les volumes associés. Ne l'utilise pas si tu souhaites conserver les données de la base.

### 4.6. Profils optionnels

Si ces profils sont déclarés dans le fichier Compose :

```bash
# Tests automatisés
docker compose --profile test run --rm api-tests
```

```bash
# MLflow
docker compose --profile mlflow up -d
```

La présence et le nom des services optionnels doivent être confirmés dans `docker-compose.yml`.

---

## 5. URLs locales

Les adresses suivantes sont les adresses documentées pour l'environnement local. Les ports réellement publiés doivent être confirmés dans la configuration Docker Compose.

| Service             | URL ou adresse                                    |
| ------------------- | ------------------------------------------------- |
| API FastAPI         | `http://127.0.0.1:8000`                           |
| Swagger UI          | `http://127.0.0.1:8000/docs`                      |
| ReDoc               | `http://127.0.0.1:8000/redoc`                     |
| OpenAPI JSON        | `http://127.0.0.1:8000/openapi.json`              |
| Healthcheck         | `http://127.0.0.1:8000/health`                    |
| Frontend React/Vite | `http://127.0.0.1:3000` — à confirmer             |
| PostgreSQL          | `localhost:5433` — à confirmer                    |
| MongoDB             | `localhost:27018` — à confirmer                   |
| Redis               | `localhost:6379` — à confirmer                    |
| Kafka               | `localhost:9092` — à confirmer                    |
| MLflow              | `http://localhost:5000` — si le profil est activé |

Swagger permet d'examiner les routes, les schémas de requêtes et les réponses documentées lorsque l'API est démarrée.

---

## 6. Configuration

Les variables d'environnement sont documentées dans `.env.example` et dans la configuration backend. Les noms exacts et les valeurs effectivement utilisées doivent être vérifiés dans `api/core/config.py` et dans le fichier Compose.

### 6.1. Variables principales

| Variable                   | Rôle                                           | Exemple indicatif                                    |
| -------------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| `APP_NAME`                 | Nom de l'API                                   | `DataFlow360 API`                                    |
| `APP_VERSION`              | Version applicative                            | `0.1.0`                                              |
| `ENVIRONMENT`              | Environnement d'exécution                      | `development`                                        |
| `CORS_ALLOWED_ORIGINS`     | Origines frontend autorisées                   | `http://localhost:3000,http://localhost:5173`        |
| `SIMULATION_ENABLED`       | Active le mode simulation si prévu par le code | `true`                                               |
| `DATABASE_URL`             | Connexion PostgreSQL                           | `postgresql+psycopg://...`                           |
| `MONGO_URL`                | Connexion MongoDB, si utilisée                 | `mongodb://...`                                      |
| `REDIS_URL`                | Connexion Redis, si utilisée                   | `redis://redis:6379/0`                               |
| `FRAUD_MODEL_PATH`         | Chemin du modèle fraude                        | `/app/models/fraude/modele_fraude_final.pkl`         |
| `FRAUD_MODEL_VERSION`      | Version déclarée du modèle fraude              | `local`                                              |
| `FRAUD_DECISION_THRESHOLD` | Seuil de classification fraude                 | `0.5`                                                |
| `CREDIT_MODEL_PATH`        | Chemin du modèle crédit                        | `/app/models/credit/modele_scoring_credit_final.pkl` |
| `CREDIT_MODEL_VERSION`     | Version déclarée du modèle crédit              | `local`                                              |
| `JWT_SECRET`               | Clé de signature des tokens                    | Secret à configurer                                  |
| `JWT_ALGORITHM`            | Algorithme JWT                                 | `HS256`                                              |
| `JWT_EXPIRES_MINUTES`      | Durée de validité du token                     | `1440`                                               |
| `KAFKA_HOST`               | Hôte Kafka interne                             | `kafka`                                              |
| `KAFKA_PORT`               | Port Kafka interne                             | `19092`                                              |
| `API_BASE_URL`             | URL de l'API vue par le consumer               | `http://api:8000`                                    |
| `SERVICE_EMAIL`            | Compte technique du consumer                   | `service-consumer@dataflow360.com`                   |
| `SERVICE_PASSWORD`         | Mot de passe du compte technique               | Valeur locale à configurer                           |

Les exemples sont indicatifs et ne remplacent pas la configuration effective du dépôt.

### 6.2. Sécurité de la configuration

* Ne jamais committer `.env`.
* Ne jamais publier un vrai mot de passe, un secret JWT ou un token d'accès.
* Utiliser `.env.example` comme modèle de configuration.
* Remplacer les identifiants de démonstration avant tout déploiement non local.
* Ne pas activer un mode simulation en production si la configuration du projet l'interdit.

---

## 7. Authentification JWT

Le backend documente une authentification reposant sur des tokens JWT.

Les routes protégées doivent être appelées avec un en-tête de la forme :

```http
Authorization: Bearer <ACCESS_TOKEN>
```

### 7.1. Routes d'authentification documentées

| Méthode | Route         | Fonction                                         |
| ------- | ------------- | ------------------------------------------------ |
| `POST`  | `/auth/login` | Connexion                                        |
| `GET`   | `/auth/me`    | Informations sur l'utilisateur connecté          |
| `POST`  | `/auth/users` | Création d'un utilisateur, selon les permissions |
| `GET`   | `/auth/users` | Liste des utilisateurs, selon les permissions    |

La liste et les permissions doivent être confirmées dans la version courante de l'API.

### 7.2. Obtenir un token

Remplacer les identifiants ci-dessous par ceux configurés dans l'environnement local.

```bash
curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=<EMAIL>" \
  --data-urlencode "password=<MOT_DE_PASSE>"
```

Si la connexion réussit, la réponse doit contenir un champ `access_token`.

Pour appeler une route protégée :

```bash
curl -i http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 7.3. Rôles

Les documents du projet mentionnent les rôles suivants :

* `admin` : administration et gestion des utilisateurs, selon les permissions du code ;
* `analyst` : accès aux fonctionnalités métier autorisées.

Le rôle `viewer` apparaît dans certains documents d'équipe, mais son implémentation réelle doit être confirmée dans le code de sécurité et les dépendances d'autorisation. Il ne faut pas présenter ce rôle comme opérationnel sans vérification.

Les identifiants de démonstration éventuellement créés par `api/scripts/seed_users.py` doivent être vérifiés dans le script et dans l'environnement avant utilisation.

---

## 8. Endpoints de l'API

> La référence effective des routes est Swagger : `http://127.0.0.1:8000/docs`. La liste ci-dessous reprend les routes documentées dans les fichiers du projet ; elle ne signifie pas que chaque endpoint a été retesté dans l'environnement actuel.

### 8.1. Santé et authentification

| Méthode | Route         | Fonction                                       |
| ------- | ------------- | ---------------------------------------------- |
| `GET`   | `/`           | Message d'accueil                              |
| `GET`   | `/health`     | État de l'API et informations de configuration |
| `POST`  | `/auth/login` | Connexion                                      |
| `GET`   | `/auth/me`    | Profil de l'utilisateur connecté               |
| `POST`  | `/auth/users` | Création d'un utilisateur                      |
| `GET`   | `/auth/users` | Liste des utilisateurs                         |

### 8.2. Clients

| Méthode | Route                  | Fonction                                                              |
| ------- | ---------------------- | --------------------------------------------------------------------- |
| `GET`   | `/clients`             | Liste des clients, selon les paramètres de pagination disponibles     |
| `GET`   | `/clients/{client_id}` | Détail d'un client et informations associées, selon le schéma courant |

### 8.3. Fraude

| Méthode | Route                      | Fonction                               |
| ------- | -------------------------- | -------------------------------------- |
| `POST`  | `/fraud/predict`           | Évaluation du risque d'une transaction |
| `GET`   | `/fraud/alerts`            | Liste des alertes                      |
| `GET`   | `/fraud/alerts/{alert_id}` | Détail d'une alerte                    |
| `PATCH` | `/fraud/alerts/{alert_id}` | Mise à jour du traitement d'une alerte |
| `GET`   | `/fraud/stats`             | Statistiques et KPI de fraude          |

### 8.4. Crédit

| Méthode | Route                                   | Fonction                                                                              |
| ------- | --------------------------------------- | ------------------------------------------------------------------------------------- |
| `POST`  | `/credit/score`                         | Scoring à partir des variables fournies                                               |
| `POST`  | `/credit/score/auto`                    | Scoring à partir de l'historique, si la route est disponible dans la version courante |
| `GET`   | `/credit/score/{application_id}`        | Dernier score associé à une demande, selon le contrat de la route                     |
| `GET`   | `/credit/applications`                  | Liste des demandes de crédit                                                          |
| `GET`   | `/credit/applications/{application_id}` | Détail d'une demande                                                                  |
| `GET`   | `/credit/stats`                         | Statistiques et KPI de crédit                                                         |

### 8.5. Format des erreurs

Le format d'erreur documenté est de la forme suivante :

```json
{
  "error": {
    "code": "validation_error",
    "message": "La requête contient des données invalides.",
    "details": [
      {
        "field": "amount",
        "message": "Input should be greater than 0",
        "type": "greater_than"
      }
    ]
  }
}
```

Les codes d'erreur et les champs exacts dépendent de l'implémentation courante. Il faut se référer aux gestionnaires d'erreurs et aux réponses réelles de l'API pour les confirmer.

---

## 9. Scoring de crédit

### 9.1. Modèle utilisé

Fichier du modèle documenté :

```text
models/credit/modele_scoring_credit_final.pkl
```

Contrat du modèle documenté :

```text
api/services/ml_contracts.py
CREDIT_MODEL_CONTRACT
```

L'intégration du modèle réel a été signalée comme fonctionnelle lors d'un essai précédent : une réponse de test avait notamment renvoyé `is_simulation: false`. Cette observation historique ne remplace pas un nouveau test dans l'environnement courant.

### 9.2. Les 15 variables documentées

Le contrat du modèle mentionne les variables suivantes :

```text
age
anciennete_compte_mois
nb_transactions_90j
montant_entrees_90j
montant_sorties_90j
solde_moyen_90j
regularite_revenus
nombre_credits_precedents
taux_remboursement
nombre_credits_en_retard
nombre_credits_impayes
montant_credit_demande
duree_credit_demande
stabilite_flux
type_activite
```

Le nom, le type, l'ordre et l'échelle de ces variables doivent rester cohérents entre les données d'entraînement et les données envoyées au modèle.

### 9.3. Scoring manuel — `POST /credit/score`

Cette route est documentée comme permettant de fournir les variables attendues par le contrat du modèle.

Elle peut être utilisée pour tester l'intégration entre l'API, le service de scoring et le modèle ML.

Le corps de requête exact doit être récupéré depuis le schéma Pydantic courant ou Swagger avant de lancer un test.

### 9.4. Scoring automatique — `POST /credit/score/auto`

Cette route est documentée comme prenant quatre champs :

```json
{
  "account_id": "CLI-000001",
  "montant_credit_demande": 200000,
  "duree_credit_demande": 6,
  "type_activite": "commerce"
}
```

Le principe est de récupérer l'historique du client et de calculer des variables comportementales avant d'appeler le modèle.

Les documents disponibles ne sont pas parfaitement cohérents sur le nombre de variables calculées automatiquement : certains indiquent 11 variables calculées, tandis qu'une autre version documente 12 variables calculées et 3 variables métier saisies, pour arriver à 15 variables au total.

**Le calcul exact doit être confirmé dans `api/repositories/credit_repository.py`, `api/schemas/credit.py`, `api/services/credit_service.py` et dans le contrat ML.** Il ne faut pas considérer le total de 15 comme confirmé tant que le code actuel n'a pas été comparé au modèle.

### 9.5. Échelles et préparation des variables

Les documents antérieurs indiquent des valeurs entre 0 et 100 pour certaines variables, notamment :

* `regularite_revenus` ;
* `stabilite_flux` ;
* `taux_remboursement`.

Cependant, des exemples de tests antérieurs utilisaient également des valeurs comme `0.9` et `0.95`.

Cette différence d'échelle doit être résolue en comparant :

1. les données d'entraînement ;
2. le code de calcul des variables ;
3. le contrat du modèle ;
4. les valeurs effectivement envoyées au modèle en production ou en démonstration.

Les formules exactes de `regularite_revenus` et de `stabilite_flux` ne sont pas affirmées ici, faute de confirmation suffisante dans le code consulté.

### 9.6. Interprétation du score

Une règle métier précédemment documentée utilise un seuil de `0.90` :

```text
score >= 0.90  → eligible = true
score <  0.90  → eligible = false
```

Cette règle doit être confirmée dans le code actuel et validée par l'équipe Data Science. Il faut notamment vérifier à quelle classe du modèle correspond la probabilité utilisée.

Le seuil ne doit pas être présenté comme une règle universelle de décision financière.

### 9.7. Explicabilité

Le champ `explanation_factors` a précédemment été observé à `null`.

Les explications détaillées des scores ne doivent donc pas être présentées comme disponibles tant que leur implémentation et leurs résultats n'ont pas été vérifiés.

---

## 10. Détection de fraude

### 10.1. Modèle utilisé

Fichier du modèle documenté :

```text
models/fraude/modele_fraude_final.pkl
```

Contrat du modèle documenté :

```text
api/services/ml_contracts.py
FRAUD_MODEL_CONTRACT
```

Le modèle de fraude a été signalé comme intégré au backend lors de tests précédents. Il reste nécessaire de vérifier que le modèle réel est chargé dans l'environnement actuel.

### 10.2. Variables du modèle

Les documents décrivent huit variables :

```text
montant
heure
ecart_montant_moyen
ecart_heure_habituelle
nouvel_appareil
nouveau_destinataire
type
canal
```

Les valeurs attendues pour `type`, `canal` et les variables catégorielles doivent correspondre au contrat du modèle et au prétraitement appliqué pendant l'entraînement.

### 10.3. Endpoint `POST /fraud/predict`

Le fonctionnement documenté est le suivant :

1. Validation des données reçues.
2. Préparation des variables attendues par le modèle.
3. Chargement du modèle de fraude.
4. Calcul du score de risque.
5. Attribution d'un niveau de risque selon les règles configurées.
6. Persistance des données et d'une alerte selon les règles métier applicables.

Le champ `is_simulation`, lorsqu'il est présent dans la réponse, permet de distinguer une prédiction en simulation d'une prédiction effectuée avec le modèle réel.

La persistance des alertes de niveau `HIGH` est documentée comme une règle du backend. Elle doit être confirmée par un test HTTP et une vérification en base.

### 10.4. Statuts des alertes

Les statuts documentés sont :

| Statut      | Signification                     |
| ----------- | --------------------------------- |
| `pending`   | Alerte créée et non traitée       |
| `reviewed`  | Alerte examinée par un analyste   |
| `confirmed` | Suspicion confirmée après analyse |
| `dismissed` | Alerte écartée après examen       |

Les transitions réellement autorisées doivent être confirmées dans le schéma et le service de gestion des alertes.

### 10.5. Statistiques de fraude

Les documents du projet mentionnent notamment les indicateurs suivants :

| Indicateur             | Signification attendue                       |
| ---------------------- | -------------------------------------------- |
| `total_transactions`   | Nombre de transactions prises en compte      |
| `total_alerts`         | Nombre d'alertes enregistrées                |
| `suspicious_rate`      | Ratio défini par l'implémentation            |
| `suspicious_amount`    | Montant associé aux transactions alertées    |
| `alerts_by_status`     | Répartition des alertes par statut           |
| `alerts_by_risk_level` | Répartition des alertes par niveau de risque |
| `alerts_evolution`     | Évolution des alertes dans le temps          |

Les noms et les formules de ces indicateurs doivent être confirmés sur la réponse actuelle de `/fraud/stats`.

---

## 11. Pipeline Kafka temps réel

### 11.1. Principe

Le pipeline Kafka documenté suit ce parcours :

```text
Transaction Producer
        |
        v
Kafka topic "transactions.raw"
        |
        v
Fraud Consumer
        |
        | Requête HTTP avec JWT
        v
POST /fraud/predict
        |
        v
Modèle de fraude
        |
        v
Enregistrement d'une alerte
si les conditions métier sont satisfaites
```

### 11.2. Responsabilité des composants

| Composant        | Responsabilité                                                |
| ---------------- | ------------------------------------------------------------- |
| Producer         | Publier les transactions dans Kafka                           |
| Kafka            | Transporter les messages vers le consumer                     |
| Consumer         | Lire les messages et appeler l'API                            |
| API FastAPI      | Valider la transaction et déclencher la prédiction            |
| Modèle de fraude | Évaluer le risque                                             |
| PostgreSQL       | Conserver les données et alertes selon les règles configurées |

Les fichiers documentés du pipeline sont :

```text
streaming/producer.py
streaming/consumer.py
streaming/Dockerfile
```

Le topic documenté est :

```text
transactions.raw
```

### 11.3. Vérifier le fonctionnement

Vérifier les services :

```bash
docker compose ps -a
```

Consulter les logs du producer :

```bash
docker compose logs --tail=100 transaction-producer
```

Consulter les logs du consumer :

```bash
docker compose logs --tail=100 fraud-consumer
```

Après authentification, consulter les alertes :

```bash
TOKEN="<ACCESS_TOKEN>"

curl -i "http://127.0.0.1:8000/fraud/alerts" \
  -H "Authorization: Bearer $TOKEN"
```

Pour confirmer le fonctionnement de bout en bout, il faut vérifier que :

* le producer publie des messages ;
* le consumer reçoit les messages ;
* le consumer peut joindre l'API ;
* l'authentification du compte technique fonctionne ;
* les prédictions sont exécutées ;
* les alertes attendues sont effectivement enregistrées en base.

La présence des conteneurs ne suffit pas à prouver que tout le pipeline fonctionne correctement.

---

## 12. Base de données et données synthétiques

### 12.1. Tables documentées

Les six tables principales documentées utilisent le préfixe `api_` :

| Table                     | Contenu                                |
| ------------------------- | -------------------------------------- |
| `api_users`               | Comptes et authentification            |
| `api_clients`             | Informations sur les clients           |
| `api_transactions`        | Transactions                           |
| `api_fraud_alerts`        | Alertes de fraude                      |
| `api_credit_applications` | Demandes de crédit                     |
| `api_credit_scores`       | Scores de crédit associés aux demandes |

Les noms, colonnes, relations et contraintes effectifs doivent correspondre à `api/db/models.py` et aux migrations réellement exécutées.

### 12.2. Initialisation

Les scripts documentés sont :

```text
api/scripts/init_db.py
api/scripts/generate.py
api/scripts/seed_users.py
```

Ils sont associés à l'initialisation de la base, à la génération de données synthétiques et à la création de comptes de démonstration.

### 12.3. Volumes de données

Une version de la documentation décrit les volumes suivants :

* environ **500 clients** ;
* environ **23 750 transactions** ;
* environ **1 900 alertes** ;
* environ **750 demandes de crédit**.

Ces chiffres correspondent aux volumes documentés dans une version du script de génération. Ils ne doivent être considérés comme les volumes réellement présents dans la base que si le seed courant et les données chargées ont été vérifiés.

Une autre documentation d'équipe mentionne environ 10 000 transactions et 800 alertes. Cette divergence doit être résolue en vérifiant la version du script, la configuration du seed et le contenu de la base.

### 12.4. Taux d'alertes et distribution du modèle

La documentation du seed mentionne environ 8 % d'alertes, tandis qu'une distribution de prédictions du modèle a été décrite comme comportant environ 20 % de résultats `HIGH`.

Ces proportions ne sont pas nécessairement comparables : l'une peut représenter une proportion définie lors de la génération des données, tandis que l'autre peut représenter la proportion de prédictions classées à risque élevé.

Avant de les comparer, il faut préciser :

* le dénominateur utilisé ;
* le jeu de données concerné ;
* le seuil de classification appliqué ;
* si les alertes sont générées artificiellement ou enregistrées à partir des prédictions ;
* si les statistiques concernent le seed, le jeu de test ML ou les données de la base courante.

Aucun taux unique ne doit être présenté sans préciser son périmètre.

---

## 13. Chargement des modèles ML

### 13.1. Chaîne de chargement

Le mécanisme documenté est le suivant :

```text
Configuration (.env)
        |
        v
Settings
        |
        v
Service métier
        |
        v
Chargement du modèle
        |
        v
Préparation des variables
        |
        v
Prédiction
        |
        v
Score de risque
```

Le fichier de chargement documenté est :

```text
api/services/model_loader.py
```

Les modèles sont stockés dans le répertoire `models/`.

### 13.2. Contrats ML

Les contrats des modèles sont documentés dans :

```text
api/services/ml_contracts.py
```

Les contrats définissent notamment les variables attendues par chaque modèle.

Le respect du nom et de l'ordre des colonnes est essentiel pour éviter les erreurs de prétraitement et garantir que les données transmises correspondent à celles utilisées pendant l'entraînement.

### 13.3. Points de vigilance

* Vérifier la présence des fichiers `.pkl` dans l'environnement d'exécution.
* Vérifier que les chemins configurés correspondent aux fichiers réels.
* Vérifier la compatibilité entre les versions des bibliothèques et celles utilisées lors de l'entraînement.
* Vérifier les types, les valeurs manquantes et l'ordre des variables.
* Redémarrer l'API après le remplacement d'un modèle si le mécanisme de chargement ne prévoit pas de rechargement à chaud.
* Ne pas confondre un chargement réussi avec une validation de la qualité prédictive du modèle.

---

## 14. Tests et état des vérifications

Cette section distingue les vérifications rapportées précédemment des contrôles restant à effectuer. **Elle ne signifie pas que l'ensemble des tests automatisés a réussi.**

### 14.1. État documenté au 9 octobre 2026

| Élément                               | État documenté                              | Précision                                                                                                        |
| ------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Chargement du modèle crédit           | Vérifié lors d'un essai précédent           | Le modèle réel avait été chargé dans un test antérieur.                                                          |
| `POST /credit/score` avec modèle réel | Vérifié lors d'un essai précédent           | Une réponse avait renvoyé un score avec `is_simulation: false`.                                                  |
| Intégration du modèle fraude          | Signalée fonctionnelle précédemment         | Un nouveau test reste nécessaire dans l'environnement courant.                                                   |
| Démarrage de tous les conteneurs      | À confirmer                                 | Une sortie partielle montrait un service d'initialisation en état `Exited`.                                      |
| `GET /health`                         | Non confirmé dans l'environnement courant   | La sortie précédemment partagée ne permettait pas de confirmer clairement le statut HTTP et le corps de réponse. |
| `GET /openapi.json`                   | Non confirmé dans l'environnement courant   | Aucune sortie exploitable n'avait été partagée.                                                                  |
| Liste actuelle des routes             | À vérifier                                  | L'extraction précédente des routes n'avait pas fourni de résultat exploitable.                                   |
| Authentification JWT                  | À retester                                  | Aucun résultat récent complet n'est consigné ici.                                                                |
| Pipeline Kafka de bout en bout        | À retester                                  | La présence des services ne suffit pas à confirmer le traitement réel des messages.                              |
| Suite de tests automatisés            | Résultat global non confirmé                | Il faut exécuter la suite et conserver sa sortie.                                                                |
| Métriques finales des modèles         | À documenter depuis les évaluations réelles | Les valeurs ne doivent pas être inventées.                                                                       |

### 14.2. Vérifier l'état de Docker

```bash
cd ~/Projet-Dataflow360

docker compose ps -a
```

Pour examiner les logs d'initialisation :

```bash
docker compose logs --tail=100 db-init
```

Si le nom du service diffère, le retrouver avec :

```bash
docker compose config --services
```

### 14.3. Tester le healthcheck

```bash
curl -i http://127.0.0.1:8000/health
```

Il faut vérifier le code HTTP et le corps de la réponse.

### 14.4. Vérifier OpenAPI

```bash
curl -i http://127.0.0.1:8000/openapi.json
```

Pour afficher uniquement les routes si le document est valide :

```bash
curl -fsS http://127.0.0.1:8000/openapi.json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(", ".join(sorted(v.keys())), p) for p,v in sorted(d.get("paths", {}).items())]'
```

### 14.5. Exécuter les tests automatisés

Si le service `api-tests` existe dans la configuration Docker Compose :

```bash
docker compose --profile test run --rm api-tests
```

Si les tests sont exécutés dans un environnement Python local, utiliser l'environnement virtuel approprié et la commande configurée par le projet, par exemple :

```bash
pytest -v
```

Il faut conserver la sortie réelle : nombre de tests exécutés, réussites, échecs et éventuelles erreurs de configuration.

### 14.6. Tester les modèles

Pour chaque modèle, vérifier séparément :

1. que le fichier est accessible ;
2. que le service charge le modèle ;
3. que la requête respecte le schéma attendu ;
4. que la prédiction retourne une réponse cohérente ;
5. que le mode simulation est désactivé lorsque le modèle réel est utilisé ;
6. que la persistance fonctionne lorsque la route est censée enregistrer des données.

Un test manuel réussi ne remplace pas une suite de tests automatisés ni une évaluation scientifique du modèle.

### 14.7. Métriques des modèles

Les métriques finales ne sont pas renseignées dans ce README faute de résultats d'évaluation confirmés dans les informations disponibles.

Pour le modèle de fraude, les métriques à documenter comprennent notamment :

* précision ;
* rappel ;
* F1-score ;
* ROC-AUC ;
* PR-AUC, particulièrement utile pour une classe de fraude minoritaire ;
* matrice de confusion ;
* seuil de classification utilisé.

Pour le modèle de crédit, il faut notamment documenter :

* précision ;
* rappel ;
* F1-score ;
* ROC-AUC, si adapté au problème et aux sorties du modèle ;
* matrice de confusion ;
* définition exacte de la classe positive ;
* seuil d'éligibilité et justification de ce seuil.

Les valeurs doivent provenir des notebooks ou scripts d'évaluation du modèle final et du jeu de test correspondant. Il faut préciser le jeu de données, la date ou version de l'évaluation et le seuil utilisé.

---

## 15. Intégration frontend

Le frontend React/Vite communique avec le backend par des requêtes HTTP.

Les fonctionnalités métier documentées comprennent :

* consultation des clients ;
* consultation des alertes de fraude ;
* suivi du statut des alertes ;
* soumission de transactions à l'API de détection ;
* consultation des scores de crédit ;
* consultation des indicateurs statistiques.

Le frontend ne doit pas accéder directement à PostgreSQL : les échanges de données passent par l'API.

Les routes, schémas JSON, règles d'authentification et messages d'erreur doivent être cohérents entre le frontend et le backend.

La disponibilité réelle de chaque écran dépend de l'état courant du frontend et de la présence des endpoints correspondants dans l'API.

---

## 16. Limites et prochaines étapes

### 16.1. Limites actuelles à documenter

* Les données du démonstrateur sont synthétiques.
* Les métriques finales des modèles doivent être reprises depuis les évaluations réelles.
* Les formules et échelles de certaines variables du scoring de crédit doivent être harmonisées avec le contrat du modèle.
* Le seuil de décision crédit doit être validé par l'équipe Data Science.
* La génération de données synthétiques et les prédictions du modèle doivent être distinguées dans les statistiques.
* Les rôles d'authentification et leurs permissions doivent correspondre au code réellement déployé.
* Les tests du backend et du pipeline Kafka doivent être exécutés et leurs résultats consignés.
* Les explications détaillées des scores ne doivent pas être présentées comme disponibles tant qu'elles ne sont pas effectivement implémentées et vérifiées.

### 16.2. Prochaines étapes

1. Vérifier les routes exposées dans OpenAPI.
2. Exécuter les tests automatisés et enregistrer les résultats.
3. Refaire les tests HTTP des modèles de fraude et de crédit.
4. Vérifier le pipeline Kafka de bout en bout.
5. Comparer les 15 variables du contrat de crédit avec les variables effectivement construites par le backend.
6. Harmoniser les échelles et les valeurs manquantes des variables.
7. Extraire les métriques finales des notebooks d'évaluation.
8. Réconcilier les volumes du seed et les statistiques affichées.
9. Confirmer les rôles et permissions dans le code d'authentification.
10. Mettre à jour ce README lorsque ces vérifications auront été effectuées.

---

## Conclusion

DataFlow360 fournit une architecture backend destinée à démontrer la détection de fraude et le scoring de crédit dans un contexte de mobile money. FastAPI expose les fonctionnalités métier, les services utilisent les modèles ML, PostgreSQL assure la persistance et Kafka permet de structurer le traitement des transactions en flux.

Le projet doit être évalué en distinguant clairement **les fonctionnalités implémentées, les tests réellement exécutés et les performances mesurées sur les jeux d'évaluation**. Les scores constituent des aides à la décision et les données synthétiques ne permettent pas, à elles seules, de conclure à une performance équivalente en conditions réelles.
