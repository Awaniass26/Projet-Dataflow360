# DataFlow360 Backend

DataFlow360 est un projet académique consacré aux risques du mobile money au Sénégal. Le backend fournit une API FastAPI pour consulter les clients, analyser le risque de fraude d'une transaction et consulter les données de crédit disponibles.

Les données du projet sont synthétiques. Les scores produits par l'API sont des aides à la décision : l'API ne bloque pas une transaction, n'accorde pas un crédit et ne confirme pas juridiquement une fraude.

## 1. Comprendre le backend

### À quoi sert chaque composant ?

- **Frontend React/Vite :** interface utilisée par les personnes qui consultent les clients, les scores, les alertes et les KPI. Il envoie des requêtes HTTP et affiche les réponses JSON.
- **API FastAPI :** point d'entrée HTTP. Elle reçoit les requêtes, vérifie leur forme et renvoie des réponses JSON.
- **Services métier :** logique de décision du backend. Par exemple, `FraudDetectionService` prépare les features et appelle le modèle fraude.
- **Modèles ML :** composants qui calculent un score à partir de données préparées. L'artefact fraude présent dans le dépôt est `models/fraude/modele_fraude_final.pkl`; il n'est utilisé que si `FRAUD_MODEL_PATH` le désigne et si son contrat est compatible.
- **PostgreSQL :** stockage durable des clients, transactions, alertes fraude, demandes de crédit et scores de crédit.
- **Repositories :** couche qui traduit les besoins métier en lectures ou écritures PostgreSQL.

Une API n'est pas une interface utilisateur : elle expose des routes. Une base de données conserve les données. Un modèle ML calcule un score. React/Vite présente le résultat à l'utilisateur.

### Parcours général d'une requête

```text
Frontend React/Vite
        |
        v
API FastAPI (router + validation Pydantic)
        |
        v
Service métier
        |
        +--> Modèle ML, si une prédiction est nécessaire
        |
        +--> Repository --> PostgreSQL, si des données doivent être lues ou écrites
        |
        v
Réponse JSON
        |
        v
Frontend React/Vite
```

1. React/Vite envoie une requête HTTP.
2. Le `router` choisit la fonction qui correspond à la méthode et au chemin.
3. Le `schema` valide le JSON reçu ou décrit le JSON retourné.
4. Le `service` applique la logique métier.
5. Le service appelle le modèle ML et/ou un `repository`.
6. Le repository lit ou écrit PostgreSQL lorsque cela est nécessaire.
7. FastAPI renvoie une réponse JSON au frontend.

Le frontend n'accède pas directement à PostgreSQL et n'appelle pas directement le fichier `.pkl`.

## 2. Démarrer l'API en local

### Prérequis

- Docker avec Docker Compose.
- Copier `.env.example` en `.env` pour personnaliser la configuration. Le fichier `.env` ne doit pas être commité s'il contient un mot de passe ou une autre valeur sensible.
- L'artefact `models/fraude/modele_fraude_final.pkl` est monté dans le conteneur sous `/app/models`. Pour demander une prédiction réelle, configurer `FRAUD_MODEL_PATH=models/fraude/modele_fraude_final.pkl` dans `.env`; sans chemin configuré, garder `SIMULATION_ENABLED=true` pour tester les routes en simulation.

### Lancer l'API et les dépendances

Depuis la racine de `DataFlow360` :

```bash
cp .env.example .env
docker compose up --build -d
```

Compose démarre PostgreSQL, MongoDB, Redis et l'API. Un service d'initialisation crée les tables API dans PostgreSQL avant le démarrage de l'API.

Lancer les tests API dans leur conteneur :

```bash
docker compose --profile test run --rm api-tests
```

Consulter les logs et arrêter les services :

```bash
docker compose logs -f api
docker compose down
```

- API : http://127.0.0.1:8000
- Swagger : http://127.0.0.1:8000/docs
- ReDoc : http://127.0.0.1:8000/redoc
- Healthcheck : http://127.0.0.1:8000/health

L'API est accessible sur `http://127.0.0.1:8000`, Swagger sur `http://127.0.0.1:8000/docs`, ReDoc sur `http://127.0.0.1:8000/redoc` et le healthcheck sur `http://127.0.0.1:8000/health`.

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

### Point d'entrée et dépendances

#### `api/main.py`

Initialise l'objet FastAPI, lit les réglages de démarrage, configure CORS, enregistre les gestionnaires d'erreurs et inclut les routeurs `fraud`, `credit` et `client`. Il contient aussi `/` et `/health`.

Il ne contient pas la logique du modèle fraude : cette logique appartient à `api/services/fraud_service.py`.

#### `api/dependencies.py`

Centralise les dépendances FastAPI. Une dépendance construit par exemple un `FraudDetectionService`, ouvre une session PostgreSQL ou fournit un repository.

Cette centralisation est utile pour deux raisons : les routes restent lisibles et les tests peuvent remplacer une dépendance avec `app.dependency_overrides` sans modifier le code métier.

### `api/core/`

Ce dossier contient les éléments transverses, utilisés par plusieurs fonctionnalités.

- `__init__.py` : marque `core` comme package Python. Il ne contient pas de logique métier.
- `config.py` : définit `Settings`, lit `.env` et les variables d'environnement, nettoie les origines CORS et interdit la simulation en production.
- `error_handlers.py` : transforme les erreurs de validation Pydantic, les erreurs HTTP et les exceptions métier en JSON homogène.
- `exceptions.py` : définit les exceptions applicatives et leurs codes HTTP stables, par exemple `model_not_configured`, `database_not_configured` ou `resource_not_found`.

### `api/routers/`

Un router regroupe les endpoints d'une fonctionnalité. Il reçoit les données validées, appelle un service ou un repository et construit la réponse HTTP.

- `__init__.py` : package des routeurs.
- `client.py` : expose `GET /clients` et `GET /clients/{client_id}`.
- `fraud.py` : expose `POST /fraud/predict`, `GET /fraud/alerts`, `GET /fraud/alerts/{alert_id}` et `GET /fraud/stats`.
- `credit.py` : expose `POST /credit/score`, `GET /credit/score/{application_id}`, `GET /credit/applications`, `GET /credit/applications/{application_id}` et `GET /credit/stats`.

Les routers ne doivent pas contenir les requêtes SQL détaillées ni le preprocessing ML : ces responsabilités sont déléguées aux couches suivantes.

Les fichiers `__init__.py` de `api/core`, `api/db` et `api/routers` servent à
identifier ces dossiers comme packages Python. Ils ne portent pas de logique
fonctionnelle propre.

### `api/schemas/`

Les schemas sont des modèles Pydantic. Ils vérifient les entrées reçues par HTTP et décrivent la forme des réponses. Ils empêchent par exemple un montant négatif ou une heure hors de `0..23`.

- `client.py` : réponses client, transactions d'un client et demandes de crédit associées.
- `common.py` : `RiskLevel`, `ProcessingStatus`, le format `ErrorResponse` et les réponses d'erreur communes.
- `credit.py` : `CreditApplicationInput`, réponses de scoring, demandes de crédit et KPI crédit.
- `fraud.py` : `TransactionInput`, réponse de prédiction, alerte et KPI fraude. Les huit features ML sont obligatoires dans `TransactionInput`.
- `health.py` : réponses de `/` et `/health`, notamment l'état de configuration de PostgreSQL et des modèles.

### `api/services/`

Les services coordonnent la logique métier. Une route demande une opération au service; elle ne connaît pas la manière exacte dont le modèle ou la base l'exécute.

- `credit_service.py` : gère le mode simulation du crédit et le contrat provisoire. Le modèle de scoring crédit n'est pas encore prêt ni validé pour un usage réel.
- `fraud_service.py` : construit le `DataFrame` attendu par le pipeline fraude, appelle `predict_proba`, extrait la probabilité de la classe fraude et convertit le score en `low`, `medium` ou `high` lorsque le seuil est configuré.
- `ml_contracts.py` : décrit le format de l'artefact, la méthode de prédiction et l'ordre des features. Le contrat fraude reste provisoire et doit être vérifié avec l'artefact réel; le contrat crédit est également provisoire.
- `model_loader.py` : charge et met en cache les modèles sérialisés. Il sait charger les formats `joblib` et `pickle`, mais le modèle fraude actuel est sérialisé avec joblib malgré son extension `.pkl`.

### `api/repositories/`

Un repository isole l'accès PostgreSQL du reste du backend. Le service exprime un besoin métier; le repository réalise la requête SQLAlchemy.

- `client_repository.py` : liste les clients et assemble le détail d'un client avec ses transactions et demandes de crédit.
- `fraud_repository.py` : lit les alertes, calcule les KPI fraude et persiste une transaction et une alerte `HIGH` réelle de manière idempotente.
- `credit_repository.py` : lit les demandes, les scores associés et calcule les KPI crédit. Un score réel n'est enregistré que si la demande existe déjà.

### `api/db/`

- `__init__.py` : package de la couche base de données.
- `models.py` : modèles SQLAlchemy qui représentent les tables et leurs relations.
- `session.py` : crée le moteur SQLAlchemy seulement lorsque `DATABASE_URL` existe, fournit une session par requête, commit en cas de succès et rollback en cas d'erreur.

### `api/scripts/generate.py`

Génère un dataset PostgreSQL synthétique déterministe et le réinsère dans les tables `clients`, `transactions`, `fraud_alerts`, `credit_applications` et `credit_scores`. Il n'est pas appelé automatiquement au démarrage. Attention : chaque exécution vide ces cinq tables avant de les remplir. `api/scripts/init_db.py`, lancé par Compose, crée uniquement le schéma et ne génère aucune ligne.

### `models/`

L'artefact `models/fraude/modele_fraude_final.pkl` est présent dans le dépôt. Dans le conteneur API, le dossier `models/` est monté en lecture seule au chemin `/app/models`. Le chemin de modèle doit donc être configuré relativement à `/app` ou en chemin absolu. La compatibilité du format, des features et des versions de dépendances doit être vérifiée avant de présenter ses scores comme des prédictions réelles.

## 4. Variables d'environnement

Une variable d'environnement est une valeur fournie au processus sans être codée directement dans Python. Une valeur par défaut est utilisée si aucune valeur n'est fournie. Une variable facultative peut rester vide; certaines routes renverront alors une erreur claire. Les secrets, comme les mots de passe PostgreSQL, ne doivent jamais être ajoutés au README.

| Variable | Rôle simple | Exemple non sensible | Obligatoire ? | Effet si absente ou modifiée |
| --- | --- | --- | --- | --- |
| `APP_NAME` | Nom affiché par l'API. | `DataFlow360 API` | Facultative, défaut fourni | Change les métadonnées et les réponses générales. |
| `APP_VERSION` | Version affichée par `/` et `/health`. | `0.1.0` | Facultative, défaut fourni | Change la version exposée. |
| `APP_DESCRIPTION` | Description OpenAPI de l'API. | `DataFlow360 backend` | Facultative, défaut fourni | Change la description Swagger. |
| `ENVIRONMENT` | Environnement d'exécution. Valeurs acceptées : `development`, `test`, `production`. | `development` | Facultative, défaut `development` | `production` interdit `SIMULATION_ENABLED=true`. |
| `CORS_ALLOWED_ORIGINS` | Origines frontend autorisées, séparées par des virgules. | `http://localhost:5173` | Facultative, défaut historique présent dans le code | Une origine absente sera bloquée par CORS. Adapter cette valeur à React/Vite. |
| `SIMULATION_ENABLED` | Autorise une réponse `simulated` quand un modèle n'est pas configuré. | `false` | Facultative, défaut `false` | Sans modèle et sans simulation, l'endpoint renvoie `503`. |
| `DATABASE_URL` | URL SQLAlchemy de PostgreSQL. | `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB` | Facultative au démarrage, requise pour les routes DB | Les routes dépendantes de PostgreSQL renvoient `503` si elle est absente. |
| `FRAUD_MODEL_PATH` | Chemin vers le modèle fraude. | `models/fraude/modele_fraude_final.pkl` | Facultative pour le mode simulation, requise pour une prédiction réelle | Le service simule si autorisé; sinon il renvoie `model_not_configured`. |
| `FRAUD_MODEL_VERSION` | Version descriptive du modèle fraude livré. | `1.0.0` | Facultative | Disponible dans la configuration; elle n'est pas ajoutée automatiquement à la réponse actuelle. |
| `FRAUD_DECISION_THRESHOLD` | Seuil entre `0` et `1` utilisé pour calculer `risk_level`. | `0.5` | Facultative | Sans seuil, `risk_level` reste `null`; avec une valeur invalide, la configuration est refusée. |
| `CREDIT_MODEL_PATH` | Chemin réservé au futur modèle crédit. | À laisser vide pour le moment | Ne pas renseigner tant que le modèle n'est pas prêt et validé | Avec la configuration actuelle, le scoring reste en simulation si `SIMULATION_ENABLED=true`. |
| `CREDIT_MODEL_VERSION` | Version descriptive du futur modèle crédit. | `0.1.0` | Facultative | À renseigner uniquement quand un modèle prêt est intégré ; cette valeur n'est pas renvoyée par l'API actuelle. |

Le fichier `.env.example` est la référence de configuration fournie au dépôt. Le fichier `.env` local peut contenir les vrais accès PostgreSQL et doit rester privé.

## 5. Contrat HTTP pour React/Vite

### URL de base et CORS

En local, le frontend utilise généralement :

```text
http://127.0.0.1:8000
```

Le frontend Vite du dépôt définit `VITE_API_BASE_URL` dans `frontend/src/services/api.ts`, avec `http://localhost:8000` comme valeur de repli. Les appels `fetch` de cette documentation sont des exemples d'intégration ; les services métier du frontend utilisent encore des données mockées.

Un endpoint `GET` consulte une ressource. Un endpoint `POST` envoie un JSON et déclenche une opération de calcul ou de persistance.

### Format commun des erreurs

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

Codes confirmés par le code :

- `validation_error` (`422`) : JSON invalide ou champ manquant.
- `resource_not_found` (`404`) : identifiant absent de la base.
- `model_not_configured` (`503`) : chemin de modèle absent et simulation désactivée.
- `model_load_error` (`503`) : fichier modèle absent ou impossible à charger.
- `model_prediction_error` (`500`) : le modèle n'a pas produit un résultat exploitable.
- `database_not_configured` (`503`) : `DATABASE_URL` absent.
- `database_error` (`503`) : problème d'accès ou de persistance en base.
- `not_found` (`404`) et `method_not_allowed` (`405`) : route ou méthode HTTP incorrecte.
- `internal_error` (`500`) : erreur non prévue, sans détail interne exposé au frontend.

### Général

#### `GET /`

Retourne un message de bienvenue et la version de l'API.

Réponse illustrative :

```json
{
  "message": "Bienvenue sur DataFlow360 API.",
  "version": "0.1.0",
  "docs_url": "/docs"
}
```

#### `GET /health`

Vérifie la configuration déclarée, sans tester activement la connexion réseau.

Réponse illustrative :

```json
{
  "status": "ok",
  "service": "DataFlow360 API",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-10-02T10:00:00Z",
  "configuration": {
    "database_configured": true,
    "fraud_model_configured": true,
    "credit_model_configured": false,
    "simulation_enabled": false
  }
}
```

### Endpoints API — Détection de fraude et gestion des clients

Les routes ci-dessous sont déclarées dans `api/routers/fraud.py` et `api/routers/client.py` (le nom réel du fichier est `client.py`, au singulier). Elles sont enregistrées par `api/main.py`. Les exemples React de cette section montrent comment le frontend pourrait les appeler ; les services actuels de `frontend/src/services/` utilisent encore des données mockées et ne sont pas tous raccordés à ces routes.

Toutes les réponses d'erreur utilisent l'enveloppe JSON `{"error": {"code": ..., "message": ..., "details": ...}}`. `details` n'est présent que lorsque l'erreur apporte une liste de champs, notamment pour une validation `422`.

#### Appel commun depuis React

Dans une application Vite, la base URL utilisée dans le dépôt est `VITE_API_BASE_URL`, avec `http://localhost:8000` comme valeur par défaut. L'API accepte les origines définies par `CORS_ALLOWED_ORIGINS`. Pour un frontend lancé par Vite sur le port `5173`, vérifier que `http://localhost:5173` et, si nécessaire, `http://127.0.0.1:5173` figurent dans cette variable, puis redémarrer l'API.

Les exemples suivants réutilisent ce petit helper. Il lit la réponse JSON et transmet au composant l'objet `error` de l'API en cas d'échec :

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const body = await response.json();
  if (!response.ok) throw body.error;
  return body;
}
```

### Détection de fraude

#### `POST /fraud/predict` — Évaluer une transaction

**Identification.** URL complète : `http://127.0.0.1:8000/fraud/predict`. Cette route reçoit une transaction et retourne une évaluation de risque. On l'utilise lorsqu'un écran souhaite analyser une transaction avant de présenter son résultat. Elle ne bloque, n'autorise et ne confirme jamais la transaction.

**Fonctionnement réel.**

1. FastAPI valide le JSON avec `TransactionInput`. Les champs obligatoires, types, valeurs d'énumération, montant positif et plage de l'heure sont contrôlés avant d'appeler le service.
2. `FraudDetectionService` vérifie si `FRAUD_MODEL_PATH` est configuré. Si aucun modèle n'est configuré et que `SIMULATION_ENABLED=true`, il renvoie une réponse de simulation : aucune feature n'est évaluée et aucun score n'est calculé. Si la simulation est désactivée, l'API renvoie `503 model_not_configured`.
3. Avec un modèle configuré, le service le charge avec `joblib`, construit un DataFrame de huit features et appelle actuellement `predict_proba`. Le score est la probabilité de la classe fraude, arrondie à quatre décimales.
4. Si `FRAUD_DECISION_THRESHOLD` est défini, le service classe le score selon les règles ci-dessous. Sans seuil, `risk_level` est `null`.
5. La route demande une persistance uniquement pour une prédiction **réelle** dont le niveau est `high`. Le repository vérifie/crée la transaction, puis crée au plus une alerte par identifiant de transaction. Le client indiqué par `sender_account_id` doit exister dans `clients` si la transaction doit être créée.
6. La réponse de prédiction ne contient pas `alert_id`, même lorsqu'une alerte est persistée. Il faut appeler la liste ou le détail des alertes pour retrouver l'enregistrement.

Le contrat des features est marqué provisoire dans le schéma et `ml_contracts.py`; il doit être confirmé avec l'équipe qui livre le modèle. Dans le code actuel, le vecteur envoyé au modèle est ordonné ainsi : `montant`, `heure`, `ecart_montant_moyen`, `ecart_heure_habituelle`, `nouvel_appareil`, `nouveau_destinataire`, `type`, `canal`.

**Champs de la requête JSON.** Tous sont obligatoires :

| Champ | Type | Contraintes / valeurs | Signification et utilité | Exemple |
| --- | --- | --- | --- | --- |
| `transaction_id` | chaîne | Non vide | Identifiant de la transaction ; retourné par l'API et utilisé comme clé lors d'une persistance. | `"txn_demo_001"` |
| `amount` | nombre | Strictement supérieur à `0` | Montant en FCFA ; devient la feature `montant` et est enregistré avec la transaction si une alerte réelle est persistée. | `15000` |
| `transaction_type` | chaîne (enum) | `deposit`, `withdrawal`, `transfer`, `payment` | Type de mouvement ; devient la feature `type`. | `"transfer"` |
| `channel` | chaîne (enum) | `mobile_app`, `ussd`, `agent` | Canal d'exécution ; devient la feature `canal`. | `"mobile_app"` |
| `occurred_at` | date-heure ISO 8601 | Une date-heure valide | Date de l'opération ; conservée si la transaction est persistée. Elle n'est pas envoyée comme feature au modèle actuel. | `"2026-01-15T10:30:00Z"` |
| `sender_account_id` | chaîne | Non vide | Identifiant du client expéditeur. Le repository l'utilise comme `client_id` pour relier la transaction au client. | `"CLI-000001"` |
| `recipient_account_id` | chaîne | Non vide | Identifiant du destinataire. Le champ est accepté et obligatoire, mais n'est utilisé ni dans le vecteur de features ni dans la persistance actuelle. | `"CLI-000002"` |
| `hour` | entier | De `0` à `23` | Heure utilisée comme feature `heure`. Elle est fournie séparément de `occurred_at`; le code ne vérifie pas qu'elles concordent. | `10` |
| `ecart_montant_moyen` | nombre | Aucune borne Pydantic définie | Écart du montant par rapport à la moyenne habituelle, fourni par l'appelant et transmis au modèle. | `5000` |
| `ecart_heure_habituelle` | nombre | Aucune borne Pydantic définie | Écart par rapport à l'heure habituelle, fourni par l'appelant et transmis au modèle. | `1.5` |
| `nouvel_appareil` | booléen | `true` ou `false` | Indique si l'appareil est nouveau ; feature du modèle. | `false` |
| `nouveau_destinataire` | booléen | `true` ou `false` | Indique si le destinataire est nouveau ; feature du modèle. | `true` |

**Exemple complet de requête.**

```json
{
  "transaction_id": "txn_demo_001",
  "amount": 15000,
  "transaction_type": "transfer",
  "channel": "mobile_app",
  "occurred_at": "2026-01-15T10:30:00Z",
  "sender_account_id": "CLI-000001",
  "recipient_account_id": "CLI-000002",
  "hour": 10,
  "ecart_montant_moyen": 5000,
  "ecart_heure_habituelle": 1.5,
  "nouvel_appareil": false,
  "nouveau_destinataire": true
}
```

`sender_account_id` doit désigner un client existant si une alerte réelle `high` doit être enregistrée. Les identifiants d'exemple `CLI-000001` et `CLI-000002` correspondent au format produit par le générateur PostgreSQL du projet, mais leur présence dépend du chargement des données.

**Exemples de réponse.** Sans modèle configuré, le résultat habituel en mode simulation est :

```json
{
  "transaction_id": "txn_demo_001",
  "risk_score": null,
  "risk_level": null,
  "status": "simulated",
  "is_simulation": true,
  "message": "SIMULATION : aucun modèle de détection de fraude n'est encore branché. Cette réponse ne reflète aucune analyse réelle de la transaction 'txn_demo_001'."
}
```

Avec un modèle configuré, une réponse réelle peut ressembler à ceci :

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

| Champ retourné | Type | Explication |
| --- | --- | --- |
| `transaction_id` | chaîne | Identifiant reçu dans la requête. |
| `risk_score` | nombre ou `null` | Score entre `0` et `1` produit par le modèle réel ; `null` en simulation. Un score élevé est une estimation du risque, pas une preuve de fraude. |
| `risk_level` | `low`, `medium`, `high` ou `null` | Catégorie calculée à partir du seuil configuré ; `null` en simulation ou si aucun seuil n'est défini. |
| `status` | chaîne | `completed` pour un score du modèle, `simulated` pour une réponse simulée. |
| `is_simulation` | booléen | `true` signifie qu'aucune prédiction réelle n'a été exécutée. Le frontend doit le distinguer visuellement. |
| `message` | chaîne | Explication du résultat ou indication explicite de simulation. |

**Interprétation réelle des niveaux.** Pour un seuil `T = FRAUD_DECISION_THRESHOLD`, le code attribue `low` si `risk_score < T / 2`, `medium` si `T / 2 <= risk_score < T`, et `high` si `risk_score >= T`. Ces seuils sont provisoires. Le niveau `high` exprime une estimation du modèle, pas la confirmation d'une fraude.

**Quand une alerte est-elle créée ?** La condition de la route est simultanément : modèle réel (`is_simulation=false`) et `risk_level=high`. Les niveaux `low` et `medium`, ainsi que toute simulation, ne créent pas d'alerte. Pour une prédiction `high`, si PostgreSQL n'est pas configuré, la route renvoie `503 database_not_configured`. Si le client expéditeur n'existe pas lors de la création de la transaction, le repository renvoie `503 database_error`. Une alerte déjà associée à cet identifiant de transaction n'est pas dupliquée ni mise à jour. La route peut donc retourner un score sans qu'une nouvelle alerte apparaisse.

**Erreurs possibles.**

| HTTP | Code | Cause dans le code |
| --- | --- | --- |
| `422` | `validation_error` | Champ absent ou invalide : montant nul/négatif, heure hors `0..23`, type ou canal inconnu, date incorrecte, etc. |
| `503` | `model_not_configured` | `FRAUD_MODEL_PATH` absent et mode simulation désactivé. |
| `503` | `model_load_error` | Artefact configuré mais absent ou impossible à charger. |
| `500` | `model_prediction_error` | Le modèle ne renvoie pas un résultat exploitable. |
| `503` | `database_not_configured` | Un résultat réel `high` doit être persisté, mais `DATABASE_URL` est absent. |
| `503` | `database_error` | Le client expéditeur requis pour persister la transaction est absent. |
| `500` | `internal_error` | Erreur inattendue non transformée en erreur métier ; les détails internes ne sont pas exposés. |

Exemple de validation `422` réellement utilisé par le gestionnaire d'erreurs :

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

**Utilisation React.** La réponse permet d'afficher le score et le niveau lorsqu'ils ne sont pas `null`, mais le frontend doit d'abord contrôler `is_simulation`. Cette requête n'implique pas qu'une alerte a été enregistrée.

```javascript
const result = await apiRequest("/fraud/predict", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(transaction),
});
if (result.is_simulation) showSimulationNotice(result.message);
else showRisk(result.risk_score, result.risk_level);
```

#### `GET /fraud/alerts` — Lister les alertes enregistrées

**Identification.** URL complète : `http://127.0.0.1:8000/fraud/alerts`. À utiliser pour afficher l'historique des alertes réellement stockées, par exemple dans l'écran Fraude. Cette route ne renvoie pas toutes les prédictions : elle lit uniquement `fraud_alerts`.

**Fonctionnement.** FastAPI valide `limit`, ouvre une session PostgreSQL, puis le repository trie les alertes par `created_at` décroissant et retourne au plus `limit` éléments. Il n'existe actuellement ni paramètre `offset`, ni curseur de pagination.

**Paramètres.**

| Nom | Emplacement / type | Obligatoire | Règles | Signification |
| --- | --- | --- | --- | --- |
| `limit` | Query, entier | Non | Défaut `50`, minimum `1`, maximum `100` | Nombre maximal d'alertes à retourner. Ce n'est pas une pagination par pages : aucune position de départ n'est proposée. |

**Exemple de requête.** `GET /fraud/alerts?limit=20` n'a pas de corps JSON.

**Réponse représentative.**

```json
[
  {
    "alert_id": 1,
    "transaction_id": "txn_demo_001",
    "risk_score": 0.91,
    "risk_level": "high",
    "created_at": "2026-01-15T10:31:00Z"
  }
]
```

La réponse est un tableau : il peut être vide (`[]`). Chaque objet contient :

| Champ | Type | Explication |
| --- | --- | --- |
| `alert_id` | entier | Identifiant de l'alerte dans la base. |
| `transaction_id` | chaîne | Identifiant de la transaction liée. |
| `risk_score` | nombre | Score conservé avec cette alerte. |
| `risk_level` | chaîne enum | Niveau stocké (`low`, `medium` ou `high`). Les alertes créées par la route de prédiction sont `high`. |
| `created_at` | date-heure ISO 8601 | Date de création enregistrée dans PostgreSQL. |

**Erreurs possibles.** `422 validation_error` si `limit` n'est pas un entier dans `1..100` (par exemple `0` ou `101`) ; `503 database_not_configured` si PostgreSQL n'est pas configuré ; une erreur inattendue de connexion peut apparaître comme `500 internal_error`.

**Utilisation React.** Afficher `[]` comme un état vide et ne pas le confondre avec une erreur :

```javascript
const alerts = await apiRequest("/fraud/alerts?limit=20");
setAlerts(alerts);
```

#### `GET /fraud/alerts/{alert_id}` — Consulter une alerte

**Identification.** URL complète : `http://127.0.0.1:8000/fraud/alerts/1`. À utiliser lorsqu'une personne ouvre une alerte depuis une liste.

**Fonctionnement.** FastAPI convertit `alert_id` en entier, le repository cherche la clé primaire dans PostgreSQL, puis la route retourne l'alerte ou lève `resource_not_found` si elle n'existe pas.

**Paramètre d'URL.**

| Nom | Type | Obligatoire | Signification | Exemple |
| --- | --- | --- | --- | --- |
| `alert_id` | entier | Oui | Identifiant numérique retourné dans `GET /fraud/alerts`. | `1` |

**Exemple de requête.** `GET /fraud/alerts/1`, sans corps ni paramètre de requête.

**Réponse.** Le corps est un seul objet `FraudAlertResponse` :

```json
{
  "alert_id": 1,
  "transaction_id": "txn_demo_001",
  "risk_score": 0.91,
  "risk_level": "high",
  "created_at": "2026-01-15T10:31:00Z"
}
```

| Champ | Type | Explication |
| --- | --- | --- |
| `alert_id` | entier | Identifiant numérique de cette alerte. |
| `transaction_id` | chaîne | Identifiant de la transaction liée. |
| `risk_score` | nombre | Score de risque conservé avec l'alerte. |
| `risk_level` | `low`, `medium` ou `high` | Niveau de risque enregistré. |
| `created_at` | date-heure ISO 8601 | Date de création de l'alerte dans PostgreSQL. |

**Erreurs possibles.** `422 validation_error` si `alert_id` n'est pas un entier ; `404 resource_not_found` si aucune alerte porte cet identifiant ; `503 database_not_configured` si PostgreSQL n'est pas configuré ; `500 internal_error` pour une erreur inattendue.

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Aucune alerte trouvée pour '999'."
  }
}
```

**Utilisation React.** Le frontend réutilise l'identifiant sélectionné dans la liste :

```javascript
const alert = await apiRequest(`/fraud/alerts/${alertId}`);
setSelectedAlert(alert);
```

#### `GET /fraud/stats` — Consulter les indicateurs fraude

**Identification.** URL complète : `http://127.0.0.1:8000/fraud/stats`. À utiliser pour alimenter les indicateurs ou graphiques d'un écran fraude ou dashboard. Les résultats viennent de PostgreSQL, et non des mocks du frontend.

**Fonctionnement.** Le repository compte les lignes de `transactions` et `fraud_alerts`, somme le montant des transactions jointes à une alerte, regroupe les alertes par niveau et agrège leur nombre et leur montant par jour de création. L'évolution est triée par date croissante. Il n'y a ni paramètre, ni corps de requête.

**Exemple de requête.** `GET /fraud/stats`.

**Réponse représentative.** Ces valeurs illustrent des résultats cohérents, elles ne sont pas garanties dans votre base :

```json
{
  "total_transactions": 10,
  "total_alerts": 2,
  "suspicious_rate": 0.2,
  "suspicious_amount": 30000.0,
  "alerts_by_risk_level": {
    "low": 0,
    "medium": 1,
    "high": 1
  },
  "alerts_evolution": [
    {
      "date": "2026-01-15",
      "alert_count": 2,
      "suspicious_amount": 30000.0
    }
  ]
}
```

| Champ | Type | Calcul / signification |
| --- | --- | --- |
| `total_transactions` | entier | Nombre de lignes dans `transactions`. |
| `total_alerts` | entier | Nombre de lignes dans `fraud_alerts`. |
| `suspicious_rate` | nombre entre normalement `0` et `1` | `total_alerts / total_transactions`, ou `0.0` si aucune transaction. C'est la part ayant une alerte enregistrée, pas un taux de fraude confirmée. |
| `suspicious_amount` | nombre | Somme de `transactions.amount` pour les transactions jointes à une alerte. Ce n'est pas la somme des scores. |
| `alerts_by_risk_level` | objet de compteurs | Nombre d'alertes par niveau ; les clés `low`, `medium`, `high` sont initialisées à `0`. |
| `alerts_evolution` | tableau d'objets | Agrégats par date de `fraud_alerts.created_at`, triés du plus ancien au plus récent. |
| `alerts_evolution[].date` | date `YYYY-MM-DD` | Jour de création de l'alerte. |
| `alerts_evolution[].alert_count` | entier | Nombre d'alertes ce jour-là. |
| `alerts_evolution[].suspicious_amount` | nombre | Somme des montants des transactions alertées ce jour-là. |

Une prédiction simulée n'est pas enregistrée : elle ne contribue donc pas à ces statistiques. Des alertes présentes peuvent toutefois provenir du jeu de données synthétique généré, pas nécessairement d'une prédiction réelle du modèle.

**Erreurs possibles.** `503 database_not_configured` si `DATABASE_URL` est absente ; `500 internal_error` en cas d'erreur inattendue de base ou de calcul.

**Utilisation React.** Les valeurs sont déjà agrégées par l'API ; le frontend peut les afficher directement :

```javascript
const stats = await apiRequest("/fraud/stats");
setFraudStats(stats);
```

### Gestion des clients

#### `GET /clients` — Lister les clients

**Identification.** URL complète : `http://127.0.0.1:8000/clients?limit=50`. À utiliser pour remplir la liste des clients de l'application.

**Fonctionnement.** La route valide `limit`, demande au repository les clients PostgreSQL, les trie par `client_id` croissant et limite le nombre de lignes. Il s'agit d'une limite simple : aucun `offset`, curseur ou numéro de page n'est implémenté.

**Paramètre de requête.**

| Nom | Type | Obligatoire | Règles | Signification |
| --- | --- | --- | --- | --- |
| `limit` | entier | Non | Défaut `50`, minimum `1`, maximum `100` | Nombre maximal de clients à retourner. |

**Exemple de requête.** `GET /clients?limit=20`, sans corps.

**Réponse représentative.** La réponse est un tableau, éventuellement vide :

```json
[
  {
    "client_id": "CLI-000001",
    "age": 30,
    "sexe": "F",
    "region": "Dakar",
    "account_type": "standard"
  }
]
```

| Champ de chaque client | Type | Signification |
| --- | --- | --- |
| `client_id` | chaîne | Identifiant du client, utilisé dans le chemin de la route de détail. |
| `age` | entier | Âge stocké pour le client. |
| `sexe` | chaîne | Valeur de sexe stockée. |
| `region` | chaîne | Région associée au client. |
| `account_type` | chaîne | Type de compte, par exemple `standard` ou `premium`. |

**Erreurs possibles.** `422 validation_error` si `limit` est hors de `1..100` ou n'est pas un entier ; `503 database_not_configured` si PostgreSQL n'est pas configuré ; `500 internal_error` si une erreur inattendue survient.

**Utilisation React.** Le tableau peut être directement affecté à l'état de la liste :

```javascript
const clients = await apiRequest("/clients?limit=50");
setClients(clients);
```

#### `GET /clients/{client_id}` — Consulter un client et son historique

**Identification.** URL complète : `http://127.0.0.1:8000/clients/CLI-000001`. À utiliser depuis une fiche ou un lien de la liste clients.

**Fonctionnement.** La route cherche le client par sa clé primaire dans PostgreSQL. Si le client existe, le repository assemble ses attributs, ses transactions et ses demandes de crédit liées. Les alertes fraude ne sont pas incluses dans cette réponse. Si le client n'existe pas, la route renvoie `404 resource_not_found`.

**Paramètre d'URL.**

| Nom | Type | Obligatoire | Signification | Exemple |
| --- | --- | --- | --- | --- |
| `client_id` | chaîne | Oui | Identifiant exact du client enregistré dans `clients`. | `CLI-000001` |

**Exemple de requête.** `GET /clients/CLI-000001`, sans query ni corps.

**Réponse représentative.** Les tableaux `transactions` et `credit_applications` peuvent être vides :

```json
{
  "client_id": "CLI-000001",
  "age": 30,
  "sexe": "F",
  "region": "Dakar",
  "account_type": "standard",
  "transactions": [
    {
      "transaction_id": "TX-00000001",
      "amount": 15000.0,
      "type": "transfer",
      "channel": "mobile_app",
      "occurred_at": "2026-01-15T10:30:00Z"
    }
  ],
  "credit_applications": [
    {
      "application_id": "APP-00000001",
      "requested_amount": 50000.0,
      "duration": 6,
      "income": 100000.0,
      "expenses": 40000.0
    }
  ]
}
```

| Champ | Type | Explication |
| --- | --- | --- |
| `client_id` | chaîne | Identifiant du client. |
| `age` | entier | Âge stocké pour le client. |
| `sexe` | chaîne | Valeur de sexe stockée. |
| `region` | chaîne | Région associée au client. |
| `account_type` | chaîne | Type de compte du client. |
| `transactions` | tableau | Transactions reliées au client ; `[]` si aucune n'est enregistrée. |
| `transactions[].transaction_id` | chaîne | Identifiant de transaction. |
| `transactions[].amount` | nombre | Montant de transaction. |
| `transactions[].type` | chaîne | Type de transaction stocké, par exemple `transfer`. |
| `transactions[].channel` | chaîne | Canal enregistré, par exemple `mobile_app`. |
| `transactions[].occurred_at` | date-heure ISO 8601 | Date de la transaction. |
| `credit_applications` | tableau | Demandes de crédit liées au client ; `[]` si aucune n'est enregistrée. |
| `credit_applications[].application_id` | chaîne | Identifiant de la demande. |
| `credit_applications[].requested_amount` | nombre | Montant demandé. |
| `credit_applications[].duration` | entier | Durée enregistrée, en mois dans les données du projet. |
| `credit_applications[].income` | nombre | Revenus enregistrés pour la demande. |
| `credit_applications[].expenses` | nombre | Dépenses enregistrées pour la demande. |

**Erreurs possibles.** `404 resource_not_found` si aucun client ne correspond à `client_id`; `503 database_not_configured` si PostgreSQL n'est pas configuré ; `500 internal_error` si une erreur inattendue survient.

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Aucun client trouvé pour 'CLI-INCONNU'."
  }
}
```

**Utilisation React.** Prendre l'identifiant depuis la ligne sélectionnée, l'encoder pour l'URL, puis afficher les propriétés et les deux historiques :

```javascript
const client = await apiRequest(`/clients/${encodeURIComponent(clientId)}`);
setClientDetail(client);
```

### Récapitulatif fraude et clients

| Méthode | URL | Rôle | Écran frontend susceptible de l'utiliser |
| --- | --- | --- | --- |
| `POST` | `/fraud/predict` | Évalue une transaction et peut persister une alerte réelle `high`. | Formulaire d'analyse de transaction ; aucun formulaire d'envoi de transaction n'est actuellement raccordé dans le frontend. |
| `GET` | `/fraud/alerts?limit=50` | Liste les alertes persistées, les plus récentes d'abord. | Page Fraude / liste des alertes. |
| `GET` | `/fraud/alerts/{alert_id}` | Retourne le détail d'une alerte enregistrée. | Panneau ou fiche de détail d'une alerte. |
| `GET` | `/fraud/stats` | Retourne les agrégats fraude calculés depuis PostgreSQL. | KPI de la page Fraude ou du dashboard. |
| `GET` | `/clients?limit=50` | Liste au plus 100 clients, triés par identifiant. | Page Clients. |
| `GET` | `/clients/{client_id}` | Retourne les champs client, transactions et demandes de crédit. | Fiche détail client. |

Ces écrans sont des destinations d'intégration, pas la preuve que le frontend actuel appelle déjà ces routes : ses services restent en mode mock.

### Glossaire

| Terme | Explication simple |
| --- | --- |
| Endpoint / route | Adresse HTTP qui exécute une fonction de l'API. |
| Requête | Informations envoyées à l'API : chemin, paramètres, en-têtes et, pour `POST`, corps JSON. |
| Réponse | Données et code HTTP renvoyés par l'API. |
| Schéma Pydantic | Règles qui vérifient les champs et types du JSON entrant ou sortant. |
| Repository | Couche qui lit ou écrit les tables PostgreSQL pour une route. |
| Feature | Valeur préparée comme entrée du modèle de machine learning. |
| Seuil | Valeur de comparaison qui transforme un score en niveau de risque. |
| Simulation | Réponse de démonstration sans exécution du modèle ; le score et le niveau sont `null`. |
| Persistance | Enregistrement durable dans PostgreSQL. Une réponse calculée n'est pas forcément persistée. |
| CORS | Règle du navigateur qui autorise ou refuse un frontend situé sur une autre origine à appeler l'API. |

### Tester ces endpoints dans Swagger

1. Démarrer la stack depuis la racine : `docker compose up --build -d`.
2. Ouvrir <http://127.0.0.1:8000/docs> et développer le groupe `Détection de fraude` ou `Clients`.
3. Ouvrir l'opération voulue, cliquer sur **Try it out**, puis saisir les paramètres ou le JSON de la section correspondante.
4. Cliquer sur **Execute**. Swagger affiche l'URL envoyée, le code HTTP et le corps de réponse.
5. Pour les listes et statistiques, PostgreSQL doit être configuré. Pour obtenir des lignes de démonstration, exécuter d'abord `docker compose exec api python -m api.scripts.generate` ; ce script remplace les cinq tables de démonstration lorsqu'il est relancé.
6. Avec la configuration par défaut, `/fraud/predict` répond en simulation : `risk_score` et `risk_level` restent `null`, et aucune alerte n'est créée. Une prédiction réelle nécessite un modèle configuré.

### Parcours complet d'une transaction

1. Le frontend envoie le JSON complet à `POST /fraud/predict`. L'API valide les champs et exécute le modèle uniquement s'il est configuré ; sinon elle renvoie explicitement une simulation si `SIMULATION_ENABLED=true`.
2. Le frontend lit `is_simulation`. Si sa valeur est `true`, il affiche le message de simulation et n'annonce ni score réel ni alerte enregistrée.
3. Si un modèle réel renvoie `risk_level="low"` ou `"medium"`, la route retourne le score sans créer d'alerte.
4. Si le modèle réel renvoie `risk_level="high"`, la route tente de persister la transaction et l'alerte. L'enregistrement nécessite une base accessible et un `sender_account_id` présent dans `clients`. Une alerte existante pour le même `transaction_id` n'est pas dupliquée.
5. Après une réponse réelle `high`, le frontend peut rafraîchir `GET /fraud/alerts?limit=50`, puis demander `GET /fraud/alerts/{alert_id}` avec l'identifiant obtenu dans la liste.
6. Il peut enfin rafraîchir `GET /fraud/stats`. Ces KPI décrivent les transactions et alertes effectivement enregistrées ; ils ne certifient pas qu'une fraude s'est produite.

Dans l'environnement actuel sans modèle fraude configuré, l'étape 1 produit une simulation et le parcours s'arrête sans insertion automatique d'alerte. Les alertes synthétiques éventuellement visibles proviennent du générateur PostgreSQL, et non d'une prédiction réelle.

### Crédit

Le modèle de scoring de crédit n'est pas encore prêt ni validé pour un usage réel. Les routes de consultation PostgreSQL existent, mais `POST /credit/score` ne doit pas être présenté comme un score ML réel. Avec la configuration Compose par défaut (`CREDIT_MODEL_PATH` vide et simulation activée), cette route renvoie une réponse `simulated` sans calcul prédictif.

#### `POST /credit/score`

Requête :

```json
{
  "application_id": "credit_app_0001",
  "account_id": "CLI-0001",
  "requested_amount": 50000,
  "requested_duration_months": 6,
  "estimated_monthly_income": 100000,
  "estimated_monthly_expenses": 40000,
  "monthly_transaction_volume": 250000,
  "monthly_transaction_frequency": 18,
  "repayment_history_score": 0.8
}
```

Les cinq dernières features sont facultatives dans le schéma actuel pour permettre les tests du contrat provisoire. Le modèle crédit n'étant pas prêt, ne pas renseigner `CREDIT_MODEL_PATH` pour prétendre activer un vrai scoring. Avec le chemin absent et la simulation activée, la réponse ressemble à :

```json
{
  "application_id": "credit_app_0001",
  "risk_score": null,
  "risk_level": null,
  "status": "simulated",
  "is_simulation": true,
  "message": "SIMULATION : aucun modèle de scoring de crédit n'est encore branché. Cette réponse ne reflète aucune analyse réelle de la demande 'credit_app_0001'.",
  "explanation_factors": null
}
```

Une simulation ne doit pas être affichée comme un score ML. Quand le modèle crédit sera prêt, ses features, son preprocessing, ses seuils et son artefact devront être validés avant toute activation de `CREDIT_MODEL_PATH`.

#### `GET /credit/score/{application_id}`

Retourne un score crédit déjà enregistré dans `credit_scores`. Une absence renvoie `404 resource_not_found`.

```json
{
  "application_id": "credit_app_0001",
  "account_id": "CLI-0001",
  "requested_amount": 50000,
  "requested_duration_months": 6,
  "risk_score": 0.35,
  "risk_level": null,
  "created_at": "2026-10-02T10:00:00Z"
}
```

#### `GET /credit/applications?limit=50`

Liste les demandes présentes dans `credit_applications`, avec le score associé lorsqu'il existe. `limit` est compris entre `1` et `100`.

#### `GET /credit/applications/{application_id}`

Retourne une demande individuelle et son score éventuel. Une demande absente renvoie `404 resource_not_found`.

#### `GET /credit/stats`

Retourne les agrégats disponibles :

```json
{
  "total_applications": 100,
  "average_score": null,
  "average_requested_amount": 50000,
  "risk_distribution": {
    "low": 0,
    "medium": 0,
    "high": 0
  }
}
```

Le champ `default_rate` n'existe volontairement pas : les tables actuelles ne contiennent pas une observation fiable et confirmée du défaut.

## 6. Guide pratique React/Vite

Le frontend React/Vite est dans `frontend/`. `frontend/src/services/api.ts` configure Axios avec `VITE_API_BASE_URL`, dont la valeur par défaut est `http://localhost:8000`. Les exemples `fetch` de la section 5 illustrent les échanges HTTP ; ils ne signifient pas que les écrans sont déjà raccordés : les services `clients.ts`, `fraud.ts` et `dashboard.ts` retournent encore des données mockées.

Pour appeler l'API depuis le serveur Vite local, ajouter les origines du frontend à `CORS_ALLOWED_ORIGINS` dans le `.env` racine, par exemple :

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Puis recréer l'API afin qu'elle relise sa configuration :

```bash
docker compose up -d api
```

Le frontend doit gérer les états de chargement, les erreurs HTTP via `error.code`, les tableaux vides et le cas `is_simulation === true`. Les KPI (`suspicious_rate`, `suspicious_amount`, distributions et évolutions) doivent être affichés depuis les réponses statistiques de l'API, pas recalculés à partir des mocks locaux.

## 7. Base PostgreSQL et relations

Les modèles SQLAlchemy de `api/db/models.py` représentent les tables suivantes :

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

### Tables

- `clients` : identité synthétique d'un client (`client_id`, âge, sexe, région, type de compte). Un client possède plusieurs transactions et demandes de crédit.
- `transactions` : transaction mobile money (`transaction_id`, `client_id`, montant, type, canal, date). Elle appartient à un client.
- `fraud_alerts` : alerte calculée et persistée (`alert_id`, `transaction_id`, `risk_score`, `risk_level`, date). Une transaction ne possède au plus qu'une alerte selon la contrainte unique.
- `credit_applications` : demande de crédit (`application_id`, client, montant, durée, revenus, dépenses).
- `credit_scores` : résultat de scoring associé à une demande (`application_id`, score, niveau éventuel, date). Une demande ne possède au plus qu'un score selon la contrainte unique.

Les données présentes dans PostgreSQL sont durables. Les scores calculés par un service ne deviennent consultables par les routes de lecture que lorsqu'ils sont effectivement persistés.

## 8. Tests

Lancer tous les tests dans le conteneur Docker :

```bash
docker compose --profile test run --rm api-tests
```

Les tests actuels couvrent :

- `tests/test_health.py` : route racine, `/health` et route inconnue;
- `tests/test_fraud.py` : simulation, validation d'entrée, absence de modèle, alertes, KPI et identifiants inconnus;
- `tests/test_credit.py` : simulation crédit, validation et identifiants inconnus;
- `tests/test_repositories.py` : persistance idempotente fraude et agrégats crédit/fraude avec une base SQLite isolée;
- `tests/test_generator.py` : vérifie que deux générations successives en mémoire produisent les mêmes données;
- `tests/conftest.py` : fixtures communes et surcharge des dépendances FastAPI.
- `tests/__init__.py` : marque le dossier de tests comme package Python; il ne contient pas de logique de test.

Les tests unitaires ne nécessitent pas PostgreSQL ni un modèle ML réel. Les tests d'intégration manuels avec une vraie base doivent utiliser une base de développement et des identifiants de test.

## 9. Limites et responsabilités

- Le backend FastAPI valide les requêtes, exécute la logique métier et accède aux données PostgreSQL. Il appelle le modèle fraude uniquement lorsque `FRAUD_MODEL_PATH` est configuré.
- Le frontend React/Vite affiche l'interface et interprète les réponses HTTP; il ne doit pas accéder directement à PostgreSQL.
- Sans `FRAUD_MODEL_PATH`, la configuration Compose par défaut répond en simulation. L'artefact fraude existe dans le dépôt, mais son chargement et la compatibilité de son contrat doivent être vérifiés avant un usage réel.
- Le modèle de scoring crédit n'est pas encore prêt ni validé; son contrat, son preprocessing et son artefact restent à confirmer. Les réponses actuelles de scoring crédit sont simulées par défaut.
- Les données sont synthétiques et les scores sont des aides à la décision.
- Le streaming et l'infrastructure ne sont pas documentés comme des fonctionnalités du backend actuel; leur gestion relève des responsables concernés.

Quand une fonctionnalité change, mettre à jour d'abord le schema Pydantic et la route concernés, puis ce README et les tests correspondants. Toute information qui ne peut pas être confirmée par le code doit rester marquée comme à confirmer.
