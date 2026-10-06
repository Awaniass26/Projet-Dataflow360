# DataFlow360 Backend

DataFlow360 est un projet académique consacré aux risques du mobile money au Sénégal. Le backend fournit une API FastAPI pour l'authentification, la consultation des clients, l'analyse du risque de fraude, la gestion des alertes, le traitement des transactions via Kafka et la consultation des données de crédit.

Les données du projet sont synthétiques. Les scores produits par l'API sont des aides à la décision : l'API ne bloque pas une transaction, n'accorde pas un crédit et ne confirme pas juridiquement une fraude.

---

## 1. Comprendre le backend

### À quoi sert chaque composant ?

* **Frontend React/Vite :** interface utilisée par les personnes qui consultent les clients, les scores, les alertes et les KPI. Il envoie des requêtes HTTP et affiche les réponses JSON.

* **API FastAPI :** point d'entrée HTTP. Elle reçoit les requêtes, valide leur forme et renvoie des réponses JSON.

* **Services métier :** logique de décision du backend. Par exemple, `FraudDetectionService` prépare les features et appelle le modèle fraude.

* **Modèles ML :** composants qui calculent un score à partir de données préparées. L'artefact fraude présent dans le dépôt est `models/fraude/modele_fraude_final.pkl` ; il n'est utilisé que si `FRAUD_MODEL_PATH` le désigne et si son contrat est compatible.

* **PostgreSQL :** stockage durable des clients, transactions, alertes fraude, demandes de crédit et scores de crédit.

* **Repositories :** couche qui traduit les besoins métier en lectures ou écritures PostgreSQL.

Une API n'est pas une interface utilisateur : elle expose des routes. Une base de données conserve les données. Un modèle ML calcule un score. React/Vite présente le résultat à l'utilisateur.

### Parcours général d'une requête

```text

Frontend React/Vite

    |

    v

API FastAPI

(router + validation Pydantic)

    |

    v

Service métier

    |

    +--> Modèle ML, si une prédiction est nécessaire

    |

    +--> Repository --> PostgreSQL

    \|                   si des données doivent être lues/écrites

    |

    v

Réponse JSON

    |

    v

Frontend React/Vite

```

1. React/Vite envoie une requête HTTP.

2. Le `router` choisit la fonction correspondant à la méthode et au chemin.

3. Le `schema` valide le JSON reçu ou décrit le JSON retourné.

4. Le `service` applique la logique métier.

5. Le service appelle le modèle ML et/ou un `repository`.

6. Le repository lit ou écrit PostgreSQL lorsque cela est nécessaire.

7. FastAPI renvoie une réponse JSON au frontend.

Le frontend n'accède pas directement à PostgreSQL et n'appelle pas directement le fichier `.pkl`.

---

## 2. Démarrer l'API en local

### Prérequis

* Docker avec Docker Compose.

* Copier `.env.example` en `.env` pour personnaliser la configuration.

* Le fichier `.env` ne doit pas être commité s'il contient un mot de passe ou une autre valeur sensible.

* L'artefact `models/fraude/modele_fraude_final.pkl` est monté dans le conteneur sous `/app/models`.

Pour demander une prédiction réelle, configurer :

```dotenv

FRAUD_MODEL_PATH=models/fraude/modele_fraude_final.pkl

```

Sans chemin de modèle configuré, garder :

```dotenv

SIMULATION_ENABLED=true

```

pour pouvoir tester les routes en simulation.

### Lancer l'API et les dépendances

Depuis la racine de `DataFlow360` :

```bash

cp .env.example .env

docker compose up --build -d

```

Compose démarre les services nécessaires selon la configuration du projet : PostgreSQL, MongoDB, Redis, API et frontend, ainsi que les composants Kafka lorsqu'ils sont activés. Un service d'initialisation crée les tables API dans PostgreSQL.

### Lancer les tests

```bash

docker compose --profile test run --rm api-tests

```

Les tests sont exécutés dans un conteneur dédié et ne nécessitent pas PostgreSQL réel ni modèle ML réel.

### Consulter les logs

```bash

docker compose logs -f api

```

### Arrêter les services

```bash

docker compose down

```

> `docker compose down` arrête et supprime les conteneurs mais ne supprime pas les volumes persistants PostgreSQL. Ne pas utiliser `docker compose down -v` sauf si la suppression des données est volontaire.

### URLs locales

* API : `http://127.0.0.1:8000`

* Swagger : `http://127.0.0.1:8000/docs`

* ReDoc : `http://127.0.0.1:8000/redoc`

* Healthcheck : `http://127.0.0.1:8000/health`

---

## 3. Architecture réelle du dépôt

```text

api/

├── main.py

├── dependencies.py

├── core/

│   ├── __init__.py

│   ├── config.py

│   ├── error_handlers.py

│   └── exceptions.py

├── db/

│   ├── __init__.py

│   ├── models.py

│   └── session.py

├── repositories/

│   ├── client_repository.py

│   ├── credit_repository.py

│   └── fraud_repository.py

├── routers/

│   ├── __init__.py

│   ├── client.py

│   ├── credit.py

│   └── fraud.py

├── schemas/

│   ├── client.py

│   ├── common.py

│   ├── credit.py

│   ├── fraud.py

│   └── health.py

├── scripts/

│   ├── generate.py

│   └── init_db.py

└── services/

├── credit_service.py

├── fraud_service.py

├── ml_contracts.py

└── model_loader.py

models/

└── fraude/

├── modele_fraude_final.pkl

├── modele_fraude_mlflow\.py

└── model_scoring.py

tests/

├── __init__.py

├── conftest.py

├── test_credit.py

├── test_fraud.py

├── test_generator.py

├── test_health.py

└── test_repositories.py

```

### `api/main.py`

Initialise l'objet FastAPI, configure CORS, enregistre les gestionnaires d'erreurs et inclut les routeurs `fraud`, `credit` et `client`.

Il contient également :

* `GET /`

* `GET /health`

Il ne contient pas la logique du modèle fraude.

### `api/dependencies.py`

Centralise les dépendances FastAPI.

Les dépendances permettent notamment de construire les services, d'ouvrir une session PostgreSQL et de fournir les repositories.

Elles facilitent également les tests grâce à `app.dependency_overrides`.

---

## 4. Variables d'environnement

| Variable                   | Rôle                           | Exemple                                       | Obligatoire ?                      |

| -------------------------- | ------------------------------ | --------------------------------------------- | ---------------------------------- |

| `APP_NAME`                 | Nom de l'API                   | `DataFlow360 API`                             | Non                                |

| `APP_VERSION`              | Version exposée                | `0.1.0`                                       | Non                                |

| `APP_DESCRIPTION`          | Description OpenAPI            | `DataFlow360 backend`                         | Non                                |

| `ENVIRONMENT`              | Environnement                  | `development`                                 | Non                                |

| `CORS_ALLOWED_ORIGINS`     | Origines frontend autorisées   | `http://localhost:5173,http://127.0.0.1:5173` | Non                                |

| `SIMULATION_ENABLED`       | Autorise les réponses simulées | `true`                                        | Non                                |

| `DATABASE_URL`             | Connexion PostgreSQL           | `postgresql+psycopg://...`                    | Requise pour les routes DB         |

| `FRAUD_MODEL_PATH`         | Chemin du modèle fraude        | `models/fraude/modele_fraude_final.pkl`       | Requise pour une prédiction réelle |

| `FRAUD_MODEL_VERSION`      | Version descriptive du modèle  | `1.0.0`                                       | Non                                |

| `FRAUD_DECISION_THRESHOLD` | Seuil de décision fraude       | `0.5`                                         | Non                                |

| `CREDIT_MODEL_PATH`        | Chemin futur modèle crédit     | vide                                          | Non                                |

| `CREDIT_MODEL_VERSION`     | Version futur modèle crédit    | `0.1.0`                                       | Non                                |

Le fichier `.env.example` constitue la référence de configuration fournie au dépôt.

Le fichier `.env` local peut contenir les vrais accès PostgreSQL et doit rester privé.

---

# 5. Contrat HTTP

## Format commun des erreurs

Les erreurs applicatives suivent ce format :

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

Codes principaux :

* `validation_error` — `422`

* `resource_not_found` — `404`

* `model_not_configured` — `503`

* `model_load_error` — `503`

* `model_prediction_error` — `500`

* `database_not_configured` — `503`

* `database_error` — `503`

* `not_found` — `404`

* `method_not_allowed` — `405`

* `internal_error` — `500`

---

**---

6. Authentification et autorisation

Le backend utilise une authentification JWT Bearer pour protéger les routes sensibles.

Endpoints d'authentification

Méthode

URL

Accès

Fonction

POST

/auth/login

Public

Connexion et génération d'un token JWT

GET

/auth/me

Authentifié

Retourne l'utilisateur connecté

GET

/auth/users

Admin

Liste les utilisateurs

POST

/auth/users

Admin

Crée un utilisateur

L'ancien endpoint /auth/register n'est plus exposé.

Connexion

Exemple :

{
  "email": "admin@dataflow360.local",
  "password": "admin123"
}

La connexion retourne un token d'accès JWT.

Pour les routes protégées, le token doit être envoyé dans :

Authorization: Bearer <access_token>

Le backend distingue notamment les rôles admin et analyst.

Les identifiants de démonstration sont réservés à l'environnement académique/local et ne doivent pas être utilisés tels quels en production.

7. Détection de fraude**

## `POST /fraud/predict`

Évalue le risque d'une transaction.

La route :

1. valide le JSON avec `TransactionInput` ;

2. vérifie la configuration du modèle ;

3. utilise le mode simulation si aucun modèle n'est configuré et que la simulation est autorisée ;

4. sinon charge le modèle fraude ;

5. prépare les huit features ;

6. appelle `predict_proba` ;

7. calcule le `risk_score` ;

8. détermine éventuellement le `risk_level` ;

9. persiste uniquement une prédiction réelle classée `high`.

Une prédiction simulée ne crée aucune alerte.

Une prédiction réelle `low` ou `medium` retourne le score mais ne crée pas d'alerte.

Une prédiction réelle `high` tente de persister la transaction et l'alerte.

### Réponse simulée

```json

{

"transaction_id": "txn_demo_001",

"risk_score": null,

"risk_level": null,

"status": "simulated",

"is_simulation": true,

"message": "SIMULATION : aucun modèle de détection de fraude n'est encore branché."

}

```

### Réponse réelle

```json

{

"transaction_id": "txn_demo_001",

"risk_score": 0.91,

"risk_level": "high",

"status": "completed",

"is_simulation": false,

"message": "Score de risque calculé par le modèle de détection de fraude."

}

```

> `risk_score` est une estimation du modèle et ne constitue pas une preuve de fraude.

---

# 8. Gestion des alertes fraude

Les alertes représentent les résultats de fraude **réellement persistés** dans PostgreSQL.

Une alerte contient désormais :

```text

alert_id

transaction_id

risk_score

risk_level

status

explanation

reviewed_at

reviewed_by

created_at

```

### Statuts possibles

| Statut      | Signification                        |

| ----------- | ------------------------------------ |

| `pending`   | Alerte créée mais pas encore traitée |

| `reviewed`  | Alerte examinée                      |

| `confirmed` | Suspicion confirmée par l'analyste   |

| `dismissed` | Alerte écartée après analyse         |

Le statut est un élément de suivi humain : le backend ne prétend pas déterminer juridiquement qu'une fraude a eu lieu.

---

## `GET /fraud/alerts`

Liste les alertes avec pagination et filtres optionnels.

### Paramètres

| Paramètre    | Type   | Défaut | Règles                                          |

| ------------ | ------ | -----: | ----------------------------------------------- |

| `page`       | entier |    `1` | ≥ 1                                             |

| `page_size`  | entier |   `50` | entre `1` et `100`                              |

| `risk_level` | enum   |  aucun | `low`, `medium`, `high`                         |

| `status`     | enum   |  aucun | `pending`, `reviewed`, `confirmed`, `dismissed` |

### Exemples

Toutes les alertes :

```text

GET /fraud/alerts

```

Première page de 20 alertes :

```text

GET /fraud/alerts?page=1&page_size=20

```

Alertes `high` :

```text

GET /fraud/alerts?risk_level=high

```

Alertes en attente :

```text

GET /fraud/alerts?status=pending

```

Alertes `high` encore en attente :

```text

GET /fraud/alerts?risk_level=high&status=pending

```

### Réponse

```json

{

"items": [

{

  "alert_id": 816,

  "transaction_id": "txn_test_awa_suspect_001",

  "risk_score": 1.0,

  "risk_level": "high",

  "status": "confirmed",

  "explanation": "Transaction inhabituelle confirmée après vérification.",

  "reviewed_at": "2026-10-05T12:31:13.069721Z",

  "reviewed_by": "analyst_01",

  "created_at": "2026-10-04T18:25:53.500753Z"

}

],

"page": 1,

"page_size": 20,

"total": 1,

"total_pages": 1

}

```

### Champs de la réponse

| Champ         | Signification                                    |

| ------------- | ------------------------------------------------ |

| `items`       | Alertes de la page actuelle                      |

| `page`        | Numéro de page                                   |

| `page_size`   | Nombre demandé par page                          |

| `total`       | Nombre total d'alertes correspondant aux filtres |

| `total_pages` | Nombre total de pages                            |

---

## `GET /fraud/alerts/{alert_id}`

Retourne le détail d'une alerte.

Exemple :

```text

GET /fraud/alerts/816

```

Réponse :

```json

{

"alert_id": 816,

"transaction_id": "txn_test_awa_suspect_001",

"risk_score": 1.0,

"risk_level": "high",

"status": "confirmed",

"explanation": "Transaction inhabituelle confirmée après vérification.",

"reviewed_at": "2026-10-05T12:31:13.069721Z",

"reviewed_by": "analyst_01",

"created_at": "2026-10-04T18:25:53.500753Z"

}

```

Si l'alerte n'existe pas :

```json

{

"error": {

"code": "resource_not_found",

"message": "Aucune alerte trouvée pour '999'."

}

}

```

---

## `PATCH /fraud/alerts/{alert_id}`

Permet à un analyste de mettre à jour le traitement d'une alerte.

### Corps de la requête

```json

{

"status": "confirmed",

"reviewed_by": "analyst_01",

"explanation": "Transaction inhabituelle confirmée après vérification."

}

```

### Champs

| Champ         | Type             | Obligatoire | Description                                     |

| ------------- | ---------------- | ----------- | ----------------------------------------------- |

| `status`      | enum             | Oui         | `pending`, `reviewed`, `confirmed`, `dismissed` |

| `reviewed_by` | chaîne           | Oui         | Identifiant de l'analyste                       |

| `explanation` | chaîne ou `null` | Non         | Explication du traitement                       |

Lors de la mise à jour :

* `status` est modifié ;

* `reviewed_by` est enregistré ;

* `reviewed_at` est renseigné automatiquement avec l'heure UTC ;

* `explanation` est enregistrée.

Exemple :

```text

PATCH /fraud/alerts/816

```

```json

{

"status": "confirmed",

"reviewed_by": "analyst_01",

"explanation": "Transaction inhabituelle confirmée après vérification."

}

```

---

# 9. Statistiques fraude

## `GET /fraud/stats`

Retourne les KPI calculés directement depuis PostgreSQL.

### Réponse

```json

{

"total_transactions": 10062,

"total_alerts": 816,

"suspicious_rate": 0.08109719737626714,

"suspicious_amount": 202202853.68000022,

"alerts_by_status": {

"pending": 815,

"reviewed": 0,

"confirmed": 1,

"dismissed": 0

},

"alerts_by_risk_level": {

"low": 0,

"medium": 522,

"high": 294

},

"alerts_evolution": [

{

  "date": "2026-10-04",

  "alert_count": 1,

  "suspicious_amount": 10000.0

}

]

}

```

Les valeurs ci-dessus correspondent à un état de démonstration du jeu de données et peuvent évoluer.

### Indicateurs

| Champ                  | Signification                                         |

| ---------------------- | ----------------------------------------------------- |

| `total_transactions`   | Nombre total de transactions                          |

| `total_alerts`         | Nombre total d'alertes                                |

| `suspicious_rate`      | `total_alerts / total_transactions`                   |

| `suspicious_amount`    | Somme des montants des transactions liées aux alertes |

| `alerts_by_status`     | Nombre d'alertes par statut                           |

| `alerts_by_risk_level` | Nombre d'alertes par niveau                           |

| `alerts_evolution`     | Évolution quotidienne des alertes                     |

### Distribution des statuts

```json

{

"pending": 815,

"reviewed": 0,

"confirmed": 1,

"dismissed": 0

}

```

### Distribution des niveaux

```json

{

"low": 0,

"medium": 522,

"high": 294

}

```

Le nombre d'alertes par statut et le nombre d'alertes par niveau doivent chacun totaliser `total_alerts`.

---

# 10. Gestion des clients

## `GET /clients`

Liste les clients.

```text

GET /clients?limit=50

```

`limit` est compris entre `1` et `100`.

## `GET /clients/{client_id}`

Retourne un client ainsi que :

* ses informations ;

* ses transactions ;

* ses demandes de crédit.

Les alertes fraude ne sont pas directement incluses dans cette réponse.

---

# 11. Crédit

Le modèle de scoring crédit n'est pas encore prêt ni validé pour un usage réel.

Les routes de consultation PostgreSQL existent, mais `POST /credit/score` reste en simulation avec la configuration actuelle.

## `POST /credit/score`

Avec le modèle absent et la simulation activée :

```json

{

"application_id": "credit_app_0001",

"risk_score": null,

"risk_level": null,

"status": "simulated",

"is_simulation": true,

"message": "SIMULATION : aucun modèle de scoring de crédit n'est encore branché."

}

```

Il ne faut donc pas présenter cette réponse comme un véritable score ML.

Les routes de consultation disponibles sont :

* `GET /credit/score/{application_id}`

* `GET /credit/applications`

* `GET /credit/applications/{application_id}`

* `GET /credit/stats`

---

**---

12. Kafka et traitement des transactions

Le projet intègre Apache Kafka pour le transport des transactions vers le composant de détection de fraude.

Transaction
    |
    v
Kafka Producer
    |
    v
Topic : transactions
    |
    v
Fraud Consumer
    |
    v
Détection de fraude

Composants :

api/messaging/
├── kafka_producer.py
└── kafka_consumer.py

Le producer publie les transactions sur le topic transactions.

Le consumer utilise le groupe :

fraud-detection

Le consumer peut être lancé séparément :

python -m api.messaging.kafka_consumer

Le mode simulation ne doit pas être présenté comme une détection ML réelle. La persistance des alertes dépend du fonctionnement de la détection réelle et de la configuration du modèle.

13. Base PostgreSQL et relations**

```text

Client (clients)

|

+--> Transaction (transactions)

|       |

|       +--> FraudAlert (fraud_alerts, relation 0..1)

|

+--> CreditApplication (credit_applications)

      |

      +--> CreditScore (credit_scores, relation 0..1)

```

### `clients`

Informations synthétiques des clients.

### `transactions`

Transactions mobile money liées aux clients.

### `fraud_alerts`

Alertes fraude persistées.

Une transaction ne peut avoir qu'une seule alerte grâce à la contrainte unique sur `transaction_id`.

Une alerte contient notamment :

```text

alert_id

transaction_id

risk_score

risk_level

status

explanation

reviewed_at

reviewed_by

created_at

```

### `credit_applications`

Demandes de crédit.

### `credit_scores`

Scores associés aux demandes de crédit.

---

# 14. Génération des données

`api/scripts/generate.py` génère des données PostgreSQL synthétiques.

Il remplit notamment :

```text

clients

transactions

fraud_alerts

credit_applications

credit_scores

```

Le script n'est **pas exécuté automatiquement** au démarrage.

Pour le lancer :

```bash

docker compose exec api python -m api.scripts.generate

```

> Attention : chaque exécution vide les cinq tables avant de les remplir à nouveau.

`api/scripts/init_db.py`, utilisé par Compose, crée uniquement le schéma nécessaire et ne génère aucune donnée.

---

# 15. Tests

Les tests sont exécutés avec :

```bash

docker compose --profile test run --rm api-tests

```

La suite couvre actuellement les principales fonctionnalités du backend.

### `tests/test_health.py`

Teste notamment :

* `GET /`

* `GET /health`

* routes inconnues.

### `tests/test_fraud.py`

Teste notamment :

* prédiction en simulation ;

* validation des entrées ;

* montant négatif ;

* absence de modèle ;

* liste des alertes ;

* détail d'une alerte ;

* alerte inexistante ;

* statistiques fraude ;

* statuts et niveaux d'alerte.

### `tests/test_credit.py`

Teste :

* simulation crédit ;

* validation ;

* identifiants inconnus.

### `tests/test_repositories.py`

Teste notamment :

* persistance idempotente des alertes fraude ;

* agrégats fraude ;

* agrégats crédit ;

* repositories avec une base SQLite isolée.

### `tests/test_generator.py`

Vérifie que deux générations successives en mémoire produisent les mêmes données.

### Résultat attendu

La suite actuelle contient **24 tests**.

Après la mise à jour des fixtures de `tests/test_fraud.py`, la commande :

```bash

docker compose --profile test run --rm api-tests

```

doit terminer avec :

```text

24 passed

```

Un warning éventuel concernant la compatibilité `httpx`/`Starlette TestClient` n'est pas un échec de test.

---

# 16. Tester avec Swagger

1. Démarrer la stack :

```bash

docker compose up --build -d

```

2. Ouvrir :

```text

http://127.0.0.1:8000/docs

```

3. Développer les groupes :

```text

Fraud

Credit

Client

```

4. Cliquer sur **Try it out**.

5. Renseigner les paramètres ou le JSON.

6. Cliquer sur **Execute**.

Pour tester les routes PostgreSQL avec des données synthétiques :

```bash

docker compose exec api python -m api.scripts.generate

```

> Ce script remplace les données des cinq tables de démonstration.

Avec la configuration par défaut, `/fraud/predict` fonctionne en simulation si `SIMULATION_ENABLED=true`.

Dans ce cas :

```text

risk_score = null

risk_level = null

is_simulation = true

```

et aucune alerte n'est créée.

---

# 17. Parcours complet d'une alerte fraude

```text

Transaction

 |

 v

POST /fraud/predict

 |

 +---- Simulation ?

 \|       |

 \|       +--> Oui --> réponse simulée

 \|                    aucune alerte

 |

 +---- Modèle réel

         |

         v

    risk_score

         |

         v

    risk_level

         |

   +-----+-----+

   \|           |

 low/medium   high

   \|           |

   \|           v

   \|      PostgreSQL

   \|           |

   \|           v

   \|      FraudAlert

   \|           |

   +-----------+

               |

               v

      GET /fraud/alerts

               |

               v

      GET /fraud/alerts/{id}

               |

               v

      PATCH /fraud/alerts/{id}

               |

               v

         Statut traité

```

Le backend fournit donc deux niveaux distincts :

1. **Évaluation automatique du risque** par le modèle fraude.

2. **Traitement humain de l'alerte** avec statut, explication, analyste et date de revue.

Le backend ne transforme pas automatiquement une suspicion en décision juridique de fraude.

---

# 18. Guide pratique React/Vite

Le frontend React/Vite se trouve dans :

```text

frontend/

```

La variable :

```dotenv

VITE_API_BASE_URL=http://localhost:8000

```

permet de configurer l'URL de l'API.

Pour un frontend Vite lancé sur `5173`, configurer par exemple :

```dotenv

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

```

Puis redémarrer l'API afin qu'elle recharge sa configuration.

Le frontend doit gérer :

* les états de chargement ;

* les erreurs HTTP ;

* les tableaux vides ;

* les réponses `is_simulation === true` ;

* la pagination ;

* les filtres `risk_level` et `status` ;

* les détails d'une alerte ;

* la mise à jour du statut d'une alerte ;

* les KPI de fraude.

Les KPI doivent être affichés à partir de :

```text

GET /fraud/stats

```

et non recalculés à partir de données mockées.

---

# 19. Récapitulatif des endpoints

| Méthode | URL                                     | Fonction                                   |

| ------- | --------------------------------------- | ------------------------------------------ |

| `GET`   | `/`                                     | Informations générales                     |

| `GET`   | `/health`                               | État de configuration                      |

| `POST`  | `/fraud/predict`                        | Évaluer une transaction                    |

| `GET`   | `/fraud/alerts`                         | Lister les alertes avec pagination/filtres |

| `GET`   | `/fraud/alerts/{alert_id}`              | Détail d'une alerte                        |

| `PATCH` | `/fraud/alerts/{alert_id}`              | Traiter une alerte                         |

| `GET`   | `/fraud/stats`                          | KPI fraude                                 |

| `GET`   | `/clients`                              | Liste des clients                          |

| `GET`   | `/clients/{client_id}`                  | Détail client                              |

| `POST`  | `/credit/score`                         | Scoring crédit provisoire/simulé           |

| `GET`   | `/credit/score/{application_id}`        | Score crédit enregistré                    |

| `GET`   | `/credit/applications`                  | Liste des demandes                         |

| `GET`   | `/credit/applications/{application_id}` | Détail d'une demande                       |

| `GET`   | `/credit/stats`                         | KPI crédit                                 |

---

# 20. Limites et responsabilités

* Le backend FastAPI valide les requêtes, exécute la logique métier et accède aux données PostgreSQL.

* Le frontend React/Vite affiche l'interface et interprète les réponses HTTP.

* Le frontend ne doit jamais accéder directement à PostgreSQL.

* Sans `FRAUD_MODEL_PATH`, la configuration par défaut peut fonctionner en simulation.

* L'artefact fraude existe dans le dépôt, mais son contrat, ses features et sa compatibilité doivent être vérifiés avant un usage réel.

* Le modèle crédit n'est pas encore prêt ni validé.

* Les données sont synthétiques.

* Les scores sont des aides à la décision.

* Une alerte `high` est une alerte de risque, pas une preuve juridique de fraude.

* Le traitement `confirmed`, `reviewed` ou `dismissed` correspond au suivi de l'alerte par un analyste.

* Kafka est intégré au projet pour le transport des transactions ; son fonctionnement dépend de la configuration Docker et du démarrage des composants producer/consumer.

* Les données présentes dans PostgreSQL peuvent être issues du générateur synthétique et ne doivent pas être interprétées comme des données réelles de clients sénégalais.

Quand une fonctionnalité change :

1. mettre à jour le schéma Pydantic ;

2. mettre à jour le repository/service concerné ;

3. mettre à jour la route ;

4. ajouter ou adapter les tests ;

5. mettre à jour ce README.

Toute information qui ne peut pas être confirmée par le code doit rester marquée comme provisoire ou à confirmer.