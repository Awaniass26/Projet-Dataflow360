# DataFlow360 Backend

DataFlow360 est un projet académique consacré à l'analyse des risques liés au mobile money au Sénégal.

Le backend fournit une API **FastAPI** permettant notamment :

* l'authentification des utilisateurs ;
* la consultation des clients ;
* l'analyse du risque de fraude ;
* la gestion et le suivi des alertes fraude ;
* le scoring de crédit ;
* la consultation de l'historique des scores ;
* le calcul de KPI fraude et crédit ;
* la communication avec PostgreSQL.

Les données utilisées dans le projet sont **synthétiques**.

Les scores produits par les modèles sont des **aides à la décision**. Le backend ne bloque pas automatiquement une transaction, n'accorde pas automatiquement un crédit et ne constitue pas une preuve juridique de fraude.

---

# 1. Architecture générale

Le backend suit une architecture séparant les responsabilités :

```text
Frontend React/Vite
        |
        | HTTP / JSON
        v
API FastAPI
        |
        +--------------------+
        |                    |
        v                    v
   Services métier       Repositories
        |                    |
        v                    v
     Modèles ML          PostgreSQL
```

### Rôle des composants

**Frontend React/Vite**

Interface utilisée pour consulter les clients, les scores, les alertes et les KPI.

Le frontend communique avec l'API via HTTP et ne communique jamais directement avec PostgreSQL.

**API FastAPI**

Point d'entrée HTTP du backend.

Elle :

* reçoit les requêtes ;
* valide les données avec Pydantic ;
* appelle les services ;
* retourne des réponses JSON ;
* gère les erreurs applicatives.

**Services métier**

Ils contiennent la logique métier.

Exemples :

* `CreditScoringService`
* `FraudDetectionService`

Ils sont responsables notamment du chargement et de l'utilisation des modèles ML.

**Repositories**

Couche d'accès aux données PostgreSQL.

Elle permet de séparer la logique métier de la logique SQL/ORM.

**Modèles ML**

Les modèles calculent les scores à partir des données préparées.

**PostgreSQL**

Stockage durable des :

* clients ;
* transactions ;
* alertes fraude ;
* demandes de crédit ;
* scores de crédit.

---

# 2. Parcours d'une requête

Exemple pour le scoring crédit :

```text
Frontend
   |
   v
POST /credit/score
   |
   v
Pydantic
(validation)
   |
   v
CreditScoringService
   |
   v
Modèle ML
(.pkl)
   |
   v
risk_score
   |
   +--> eligible
   |
   +--> risk_level
   |
   v
CreditRepository
   |
   v
PostgreSQL
   |
   v
Réponse JSON
```

Le frontend ne connaît ni le fichier `.pkl`, ni les requêtes SQL.

---

# 3. Structure principale du backend

```text
api/
├── main.py
├── dependencies.py
│
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── error_handlers.py
│   └── exceptions.py
│
├── db/
│   ├── __init__.py
│   ├── models.py
│   └── session.py
│
├── repositories/
│   ├── client_repository.py
│   ├── credit_repository.py
│   └── fraud_repository.py
│
├── routers/
│   ├── __init__.py
│   ├── client.py
│   ├── credit.py
│   └── fraud.py
│
├── schemas/
│   ├── client.py
│   ├── common.py
│   ├── credit.py
│   ├── fraud.py
│   └── health.py
│
├── scripts/
│   ├── generate.py
│   └── init_db.py
│
└── services/
    ├── credit_service.py
    ├── fraud_service.py
    ├── ml_contracts.py
    └── model_loader.py

models/
├── credit/
│   ├── modele_scoring_credit_final.pkl
│   └── modele_scoring_mlflow.py
│
└── fraude/
    ├── modele_fraude_final.pkl
    ├── modele_fraude_mlflow.py
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

> La structure exacte peut évoluer avec le développement du projet.

---

# 4. Démarrer le backend

## Prérequis

* Docker
* Docker Compose
* Git

Créer la configuration locale :

```bash
cp .env.example .env
```

Puis lancer la stack :

```bash
docker compose up --build -d
```

Vérifier les conteneurs :

```bash
docker compose ps
```

Consulter les logs de l'API :

```bash
docker compose logs -f api
```

Arrêter la stack :

```bash
docker compose down
```

> `docker compose down` ne supprime pas les volumes persistants PostgreSQL.

Pour supprimer volontairement les volumes :

```bash
docker compose down -v
```

---

# 5. URLs locales

API :

```text
http://127.0.0.1:8000
```

Swagger :

```text
http://127.0.0.1:8000/docs
```

ReDoc :

```text
http://127.0.0.1:8000/redoc
```

Healthcheck :

```text
http://127.0.0.1:8000/health
```

---

# 6. Variables d'environnement

| Variable                   | Rôle                         | Exemple                                              |
| -------------------------- | ---------------------------- | ---------------------------------------------------- |
| `APP_NAME`                 | Nom de l'API                 | `DataFlow360 API`                                    |
| `APP_VERSION`              | Version de l'API             | `0.1.0`                                              |
| `APP_DESCRIPTION`          | Description OpenAPI          | `DataFlow360 backend`                                |
| `ENVIRONMENT`              | Environnement                | `development`                                        |
| `CORS_ALLOWED_ORIGINS`     | Origines frontend autorisées | `http://localhost:5173`                              |
| `SIMULATION_ENABLED`       | Autorise la simulation       | `true`                                               |
| `DATABASE_URL`             | Connexion PostgreSQL         | `postgresql+psycopg://...`                           |
| `FRAUD_MODEL_PATH`         | Chemin du modèle fraude      | `/app/models/fraude/modele_fraude_final.pkl`         |
| `FRAUD_MODEL_VERSION`      | Version du modèle fraude     | `1.0.0`                                              |
| `FRAUD_DECISION_THRESHOLD` | Seuil fraude                 | `0.5`                                                |
| `CREDIT_MODEL_PATH`        | Chemin du modèle crédit      | `/app/models/credit/modele_scoring_credit_final.pkl` |
| `CREDIT_MODEL_VERSION`     | Version du modèle crédit     | `0.1.0`                                              |

Le fichier `.env` contient la configuration locale et ne doit pas être commité s'il contient des informations sensibles.

---

# 7. Authentification

Le backend utilise une authentification **JWT Bearer**.

## Endpoints

| Méthode | URL           | Accès       | Fonction                       |
| ------- | ------------- | ----------- | ------------------------------ |
| `POST`  | `/auth/login` | Public      | Connexion et génération du JWT |
| `GET`   | `/auth/me`    | Authentifié | Utilisateur connecté           |
| `GET`   | `/auth/users` | Admin       | Liste des utilisateurs         |
| `POST`  | `/auth/users` | Admin       | Création d'un utilisateur      |

L'ancien endpoint `/auth/register` n'est plus exposé.

## Connexion

Exemple de requête :

```json
{
  "email": "admin@dataflow360.local",
  "password": "********"
}
```

La connexion retourne un token JWT.

Pour accéder à une route protégée :

```text
Authorization: Bearer <access_token>
```

Le backend distingue notamment les rôles :

* `admin`
* `analyst`

Les identifiants de démonstration sont réservés à l'environnement académique/local.

---

# 8. Contrat HTTP

## Format des erreurs

Les erreurs applicatives suivent le format :

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

## Principaux codes

| Code                      | HTTP | Signification                   |
| ------------------------- | ---: | ------------------------------- |
| `validation_error`        |  422 | Données invalides               |
| `resource_not_found`      |  404 | Ressource inexistante           |
| `model_not_configured`    |  503 | Modèle non configuré            |
| `model_load_error`        |  503 | Impossible de charger le modèle |
| `model_prediction_error`  |  500 | Erreur lors de la prédiction    |
| `database_not_configured` |  503 | PostgreSQL non configuré        |
| `database_error`          |  503 | Erreur base de données          |
| `not_found`               |  404 | Route ou ressource inexistante  |
| `method_not_allowed`      |  405 | Méthode HTTP non autorisée      |
| `internal_error`          |  500 | Erreur interne                  |

---

# 9. Détection de fraude

## `POST /fraud/predict`

Cette route évalue le risque associé à une transaction.

Le traitement est :

1. validation de la requête ;
2. vérification de la configuration du modèle ;
3. utilisation éventuelle du mode simulation ;
4. chargement du modèle fraude ;
5. préparation des features ;
6. appel de `predict_proba` ;
7. calcul du `risk_score` ;
8. détermination du `risk_level` ;
9. persistance éventuelle de l'alerte.

Une prédiction simulée ne crée aucune alerte.

Une prédiction réelle de niveau `high` peut entraîner la création d'une alerte persistée dans PostgreSQL.

Une alerte reste une **alerte de risque**, et non une preuve juridique de fraude.

## Réponse simulée

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

## Réponse réelle

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

---

# 10. Alertes fraude

Les alertes représentent les risques fraude réellement persistés dans PostgreSQL.

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

## Statuts

| Statut      | Signification                        |
| ----------- | ------------------------------------ |
| `pending`   | Alerte créée mais pas encore traitée |
| `reviewed`  | Alerte examinée                      |
| `confirmed` | Suspicion confirmée par l'analyste   |
| `dismissed` | Alerte écartée après analyse         |

Le statut correspond au **suivi humain** de l'alerte.

---

## `GET /fraud/alerts`

Liste les alertes avec pagination et filtres.

Paramètres :

| Paramètre    | Type   | Défaut |
| ------------ | ------ | -----: |
| `page`       | entier |    `1` |
| `page_size`  | entier |   `50` |
| `risk_level` | enum   |  aucun |
| `status`     | enum   |  aucun |

Exemple :

```text
GET /fraud/alerts?page=1&page_size=20
```

Filtre :

```text
GET /fraud/alerts?risk_level=high
```

Ou :

```text
GET /fraud/alerts?risk_level=high&status=pending
```

---

# 11. Détail et traitement d'une alerte

## `GET /fraud/alerts/{alert_id}`

Retourne le détail d'une alerte.

Exemple :

```text
GET /fraud/alerts/816
```

## `PATCH /fraud/alerts/{alert_id}`

Permet à un analyste de mettre à jour le traitement d'une alerte.

Exemple :

```json
{
  "status": "confirmed",
  "reviewed_by": "analyst_01",
  "explanation": "Transaction inhabituelle confirmée après vérification."
}
```

Lors de la mise à jour :

* le statut est modifié ;
* l'analyste est enregistré ;
* `reviewed_at` est renseigné ;
* l'explication est enregistrée.

---

# 12. Statistiques fraude

## `GET /fraud/stats`

Retourne les KPI calculés depuis PostgreSQL.

Les principaux indicateurs sont :

| Champ                  | Signification                     |
| ---------------------- | --------------------------------- |
| `total_transactions`   | Nombre total de transactions      |
| `total_alerts`         | Nombre total d'alertes            |
| `suspicious_rate`      | Taux d'alertes                    |
| `suspicious_amount`    | Montant total associé aux alertes |
| `alerts_by_status`     | Répartition par statut            |
| `alerts_by_risk_level` | Répartition par niveau            |
| `alerts_evolution`     | Évolution quotidienne             |

Les données retournées peuvent évoluer selon le contenu de PostgreSQL.

---

# 13. Gestion des clients

## `GET /clients`

Liste les clients.

Exemple :

```text
GET /clients?limit=50
```

`limit` est compris entre `1` et `100`.

## `GET /clients/{client_id}`

Retourne les informations d'un client ainsi que :

* ses transactions ;
* ses demandes de crédit.

Les alertes fraude ne sont pas directement incluses dans cette réponse.

---

# 14. Scoring crédit

Le scoring crédit est désormais connecté au **vrai modèle ML** présent dans le dépôt.

Modèle :

```text
models/credit/modele_scoring_credit_final.pkl
```

Le modèle est un pipeline `imblearn` sauvegardé avec `joblib`.

Il utilise `predict_proba`.

## Features utilisées

Le modèle utilise les 15 variables suivantes :

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

## Interprétation actuelle

La classe `1` correspond à un client **éligible**.

Le backend récupère :

```python
predict_proba(...)[0][1]
```

Ce résultat est utilisé comme `risk_score` dans l'API.

Le seuil métier actuellement configuré est :

```text
0.90
```

Ainsi :

```text
score >= 0.90  -> eligible = true
score < 0.90   -> eligible = false
```

Le seuil de 90 % doit rester considéré comme une règle métier à confirmer par l'équipe Data Science.

Le modèle fournit une aide à la décision et ne constitue pas une décision automatique d'octroi de crédit.

---

# 15. `POST /credit/score`

Cette route reçoit les caractéristiques d'une demande de crédit et calcule le score.

Exemple :

```json
{
  "application_id": "APP-00000001",
  "account_id": "CLI-000001",
  "age": 35,
  "anciennete_compte_mois": 36,
  "nb_transactions_90j": 50,
  "montant_entrees_90j": 1500000,
  "montant_sorties_90j": 600000,
  "solde_moyen_90j": 500000,
  "regularite_revenus": 0.9,
  "nombre_credits_precedents": 2,
  "taux_remboursement": 0.95,
  "nombre_credits_en_retard": 0,
  "nombre_credits_impayes": 0,
  "montant_credit_demande": 200000,
  "duree_credit_demande": 6,
  "stabilite_flux": 0.9,
  "type_activite": "commerce"
}
```

Exemple de réponse réelle :

```json
{
  "application_id": "APP-00000001",
  "risk_score": 0.0154,
  "eligible": false,
  "risk_level": "high",
  "status": "completed",
  "is_simulation": false,
  "message": "Score de risque calculé par le modèle de scoring de crédit. Seuil d'approbation : 90%.",
  "explanation_factors": null
}
```

`is_simulation: false` indique que le vrai modèle a été utilisé.

---

# 16. Historique des scores crédit

Une demande de crédit peut avoir plusieurs scores enregistrés.

Cela permet de conserver un historique des prédictions.

```text
CreditApplication
        |
        +---- CreditScore
        |
        +---- CreditScore
        |
        +---- CreditScore
```

Lors de la consultation d'une demande, le backend utilise **le dernier score** enregistré.

Le dernier score est déterminé à partir de :

1. `created_at` décroissant ;
2. puis `id` décroissant en cas d'égalité.

Cela évite les doublons dans les listes et les erreurs `MultipleResultsFound`.

---

# 17. Endpoints crédit

## `GET /credit/score/{application_id}`

Retourne le dernier score enregistré pour une demande.

## `GET /credit/applications`

Retourne la liste des demandes de crédit avec leur dernier score.

## `GET /credit/applications/{application_id}`

Retourne le détail d'une demande avec son dernier score.

## `GET /credit/stats`

Retourne les KPI crédit.

Exemple de structure :

```json
{
  "total_applications": 783,
  "average_score": 0.5126,
  "average_requested_amount": 986178.06,
  "risk_distribution": {
    "low": 96,
    "medium": 563,
    "high": 124
  },
  "validated_clients": 0
}
```

`validated_clients` correspond au nombre de clients distincts dont le dernier score atteint le seuil d'approbation configuré.

Dans l'état actuel des données, le meilleur score observé est inférieur à `0.90`, donc :

```text
validated_clients = 0
```

Cette valeur n'est pas une erreur.

---

# 18. Explicabilité du scoring crédit

Le champ :

```text
explanation_factors
```

est actuellement prévu dans la réponse API mais n'est pas encore alimenté par une méthode d'explicabilité réelle.

Il vaut actuellement :

```json
"explanation_factors": null
```

Aucun facteur ne doit être inventé à partir des seules valeurs d'entrée.

Une prochaine étape pourra utiliser une méthode telle que **SHAP**, à condition qu'elle soit réellement intégrée au modèle et validée par l'équipe Data Science.

---

# 19. PostgreSQL

Les principales entités sont :

```text
Client
 |
 +--> Transaction
 |       |
 |       +--> FraudAlert
 |
 +--> CreditApplication
         |
         +--> CreditScore
```

## Clients

Informations synthétiques des clients.

## Transactions

Transactions mobile money associées aux clients.

## FraudAlert

Alertes liées aux transactions à risque.

Une transaction ne peut avoir qu'une seule alerte grâce à la contrainte d'unicité sur `transaction_id`.

## CreditApplication

Demandes de crédit.

## CreditScore

Scores associés aux demandes.

Une demande peut avoir plusieurs scores afin de conserver l'historique.

---

# 20. Génération des données

Le script :

```text
api/scripts/generate.py
```

génère les données synthétiques PostgreSQL.

Il peut remplir notamment :

```text
clients
transactions
fraud_alerts
credit_applications
credit_scores
```

Le script n'est pas exécuté automatiquement à chaque démarrage.

Pour le lancer :

```bash
docker compose exec api python -m api.scripts.generate
```

> Attention : le générateur réinitialise les données concernées avant de les remplir à nouveau.

Le script :

```text
api/scripts/init_db.py
```

est utilisé pour initialiser le schéma de la base.

Il ne génère pas les données métier.

---

# 21. Tests

Les tests peuvent être lancés avec :

```bash
docker compose --profile test run --rm api-tests
```

La suite couvre notamment :

### `test_health.py`

* `GET /`
* `GET /health`
* routes inconnues.

### `test_fraud.py`

* simulation fraude ;
* validation ;
* montants invalides ;
* absence de modèle ;
* prédiction ;
* alertes ;
* filtres ;
* détail d'une alerte ;
* mise à jour ;
* statistiques.

### `test_credit.py`

* simulation ;
* validation des données ;
* scoring ;
* identifiants inconnus.

### `test_repositories.py`

* persistance ;
* agrégats fraude ;
* agrégats crédit ;
* gestion des derniers scores ;
* repositories avec base SQLite isolée.

### `test_generator.py`

Vérifie le comportement du générateur de données.

> Le nombre exact de tests doit être mis à jour lorsque la suite évolue. Le README ne doit pas annoncer un nombre de tests qui n'a pas été vérifié récemment.

---

# 22. Tester avec Swagger

Démarrer la stack :

```bash
docker compose up --build -d
```

Ouvrir :

```text
http://127.0.0.1:8000/docs
```

Puis :

1. développer le groupe souhaité ;
2. cliquer sur **Try it out** ;
3. renseigner les paramètres ;
4. cliquer sur **Execute** ;
5. vérifier le code HTTP ;
6. vérifier la réponse JSON.

Pour générer les données synthétiques :

```bash
docker compose exec api python -m api.scripts.generate
```

---

# 23. Frontend React/Vite

Le frontend se trouve dans :

```text
frontend/
```

L'URL de l'API peut être configurée avec :

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Pour un frontend Vite lancé sur le port `5173`, les origines doivent être autorisées côté API.

Exemple :

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Le frontend doit notamment gérer :

* les états de chargement ;
* les erreurs HTTP ;
* les réponses vides ;
* les réponses simulées ;
* la pagination ;
* les filtres ;
* les détails des alertes ;
* la mise à jour des alertes ;
* les KPI fraude ;
* les KPI crédit ;
* les demandes de crédit ;
* les scores de crédit.

Les KPI doivent être récupérés depuis l'API et non recalculés à partir de données mockées côté frontend.

---

# 24. Récapitulatif des endpoints

| Méthode | Endpoint                                | Fonction                 |
| ------- | --------------------------------------- | ------------------------ |
| `GET`   | `/`                                     | Informations générales   |
| `GET`   | `/health`                               | État de l'API            |
| `POST`  | `/auth/login`                           | Connexion                |
| `GET`   | `/auth/me`                              | Utilisateur connecté     |
| `GET`   | `/auth/users`                           | Liste des utilisateurs   |
| `POST`  | `/auth/users`                           | Création utilisateur     |
| `POST`  | `/fraud/predict`                        | Évaluer une transaction  |
| `GET`   | `/fraud/alerts`                         | Lister les alertes       |
| `GET`   | `/fraud/alerts/{alert_id}`              | Détail d'une alerte      |
| `PATCH` | `/fraud/alerts/{alert_id}`              | Traiter une alerte       |
| `GET`   | `/fraud/stats`                          | KPI fraude               |
| `GET`   | `/clients`                              | Liste des clients        |
| `GET`   | `/clients/{client_id}`                  | Détail d'un client       |
| `POST`  | `/credit/score`                         | Calculer un score crédit |
| `GET`   | `/credit/score/{application_id}`        | Dernier score            |
| `GET`   | `/credit/applications`                  | Liste des demandes       |
| `GET`   | `/credit/applications/{application_id}` | Détail d'une demande     |
| `GET`   | `/credit/stats`                         | KPI crédit               |

---

# 25. Limites actuelles

Le backend présente actuellement les limites suivantes :

* les données sont synthétiques ;
* les scores ML sont des aides à la décision ;
* un score fraude élevé n'est pas une preuve juridique de fraude ;
* le traitement d'une alerte reste humain ;
* le seuil crédit de `90 %` doit être confirmé comme règle métier finale ;
* `explanation_factors` du scoring crédit n'est pas encore implémenté ;
* l'authentification et les comptes de démonstration doivent être correctement initialisés dans l'environnement local ;
* le frontend doit être connecté aux endpoints réels ;
* les fonctionnalités doivent être testées après chaque évolution.

---

# 26. Responsabilités du backend

Le backend est responsable de :

* l'exposition des endpoints HTTP ;
* la validation des données ;
* l'authentification et l'autorisation ;
* la logique métier ;
* l'utilisation des modèles ML ;
* l'accès à PostgreSQL ;
* la persistance des scores et alertes ;
* les statistiques ;
* la gestion des erreurs ;
* les tests de l'API et des repositories.

Le frontend est responsable de l'affichage et de l'expérience utilisateur.

Le backend ne doit pas être utilisé comme une interface graphique.

---

# 27. Bonnes pratiques de développement

Lorsqu'une fonctionnalité évolue :

1. modifier le schéma Pydantic si nécessaire ;
2. modifier le service métier ;
3. modifier le repository si l'accès aux données change ;
4. modifier la route ;
5. ajouter ou adapter les tests ;
6. tester avec Swagger ;
7. vérifier les logs ;
8. mettre à jour ce README.

Les responsabilités doivent rester séparées :

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

Le modèle ML doit rester indépendant de la route HTTP.

---

# 28. État actuel du projet

## Fonctionnel

* [x] API FastAPI
* [x] PostgreSQL
* [x] Repositories
* [x] Clients
* [x] Authentification JWT
* [x] Détection fraude
* [x] Gestion des alertes
* [x] Statistiques fraude
* [x] Modèle crédit réel
* [x] Scoring crédit
* [x] Historique des scores crédit
* [x] Statistiques crédit
* [x] Swagger
* [x] Docker
* [x] Tests automatisés

## À finaliser

* [ ] Vérification complète des comptes et rôles JWT
* [ ] Test automatisé du vrai modèle crédit
* [ ] Validation définitive du seuil crédit de 90 %
* [ ] Implémentation de `explanation_factors`
* [ ] Intégration complète du frontend avec les endpoints crédit
* [ ] Validation finale de l'ensemble des tests
* [ ] Mise à jour continue de la documentation

---

# 29. Principe métier important

DataFlow360 est un système d'**aide à la décision**.

```text
Données
   ↓
Analyse
   ↓
Modèle ML
   ↓
Score de risque
   ↓
Information pour l'analyste
   ↓
Décision humaine
```

Le système ne doit donc pas être présenté comme un mécanisme automatique qui :

* bloque définitivement une transaction ;
* accuse juridiquement un client de fraude ;
* accorde automatiquement un crédit ;
* refuse automatiquement un crédit.

Les décisions finales restent sous la responsabilité humaine.
