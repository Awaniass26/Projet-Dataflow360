# DataFlow360 --- Backend

DataFlow360 est un projet académique consacré à l'analyse des risques
liés au mobile money au Sénégal. Le backend expose une API **FastAPI**
pour la gestion des clients, la détection de fraude, le scoring de
crédit et les statistiques associées.

> **Principe métier :** les scores sont des aides à la décision. Ils ne
> constituent ni une preuve juridique de fraude ni une décision
> automatique d'octroi ou de refus de crédit. Les données utilisées dans
> le projet sont synthétiques.

## Sommaire

1.  [Architecture](#1-architecture)
2.  [Démarrage](#2-démarrage)
3.  [URLs locales](#3-urls-locales)
4.  [Configuration](#4-configuration)
5.  [Authentification](#5-authentification)
6.  [Endpoints](#6-endpoints)
7.  [Scoring de crédit](#7-scoring-de-crédit)
8.  [Détection de fraude et Kafka](#8-détection-de-fraude-et-kafka)
9.  [Base de données](#9-base-de-données)
10. [Tests du backend et état des
    vérifications](#10-tests-du-backend-et-état-des-vérifications)
11. [Frontend](#11-frontend)
12. [Limites et prochaines étapes](#12-limites-et-prochaines-étapes)

------------------------------------------------------------------------

## 1. Architecture

``` text
Frontend React/Vite
        |
        | HTTP / JSON + JWT
        v
    API FastAPI
        |
        +---- Services métier ---- Modèles ML (.pkl)
        |
        +---- Repositories / SQLAlchemy
                         |
                         v
                     PostgreSQL

Pipeline fraude temps réel :
Producer -> Kafka (transactions.raw) -> Consumer
                                      |
                                      | POST /fraud/predict + JWT
                                      v
                                  API FastAPI
                                      |
                                      v
                              Modèle de fraude
                                      |
                                      v
                         PostgreSQL si risque HIGH
```

### Rôle des composants

-   **Frontend React/Vite** : interface pour consulter les clients, les
    scores, les alertes et les KPI. Il communique avec l'API, jamais
    directement avec PostgreSQL.
-   **API FastAPI** : point d'entrée HTTP, validation Pydantic,
    authentification et réponses JSON.
-   **Services métier** : logique de scoring crédit et de détection de
    fraude.
-   **Repositories** : accès à PostgreSQL via SQLAlchemy.
-   **Modèles ML** :
    -   `models/fraude/modele_fraude_final.pkl` --- pipeline de
        détection de fraude, documenté comme utilisant 8 variables.
    -   `models/credit/modele_scoring_credit_final.pkl` --- pipeline de
        scoring de crédit, documenté comme utilisant 15 variables.
-   **PostgreSQL** : stockage des utilisateurs, clients, transactions,
    alertes et scores.
-   **Kafka** : transport des transactions du producer vers le consumer.

## 2. Démarrage

### Prérequis

-   Git
-   Docker
-   Docker Compose v2

### Préparer l'environnement

Depuis la racine du dépôt :

``` bash
cd ~/Projet-Dataflow360
cp .env.example .env
```

Si `.env` existe déjà, ne l'écrase pas sans sauvegarder ta
configuration.

### Lancer les services

``` bash
docker compose up -d --build
docker compose ps -a
```

Un service d'initialisation tel que `dataflow360-db-init` peut
apparaître en état `Exited` après avoir terminé son travail. Vérifie son
code de sortie et ses logs pour confirmer que l'initialisation s'est
terminée normalement.

### Consulter les logs

``` bash
docker compose logs --tail=100 api
docker compose logs --tail=100 fraud-consumer
docker compose logs --tail=100 transaction-producer
```

Suivre les logs de l'API en direct :

``` bash
docker compose logs -f api
```

### Arrêter les services

``` bash
docker compose down
```

> **Attention :** `docker compose down -v` supprime également les
> volumes associés. Ne l'utilise pas si tu veux conserver les données de
> la base.

## 3. URLs locales

  Service       URL / adresse
  ------------- ------------------------------------------------------
  API           `http://127.0.0.1:8000`
  Swagger       `http://127.0.0.1:8000/docs`
  ReDoc         `http://127.0.0.1:8000/redoc`
  Healthcheck   `http://127.0.0.1:8000/health`
  Frontend      `http://127.0.0.1:3000` --- à confirmer avec Compose
  PostgreSQL    `localhost:5433` --- à confirmer avec Compose
  MongoDB       `localhost:27018` --- à confirmer avec Compose
  Redis         `localhost:6379` --- à confirmer avec Compose
  Kafka         `localhost:9092` --- à confirmer avec Compose

Les ports publiés peuvent varier selon le fichier `docker-compose.yml`.

## 4. Configuration

Les variables ci-dessous sont documentées dans le projet. Vérifie leurs
noms et valeurs effectives dans `.env.example`, `.env` et
`api/core/config.py`.

  -----------------------------------------------------------------------------------------------------------
  Variable                     Rôle                    Exemple indicatif
  ---------------------------- ----------------------- ------------------------------------------------------
  `APP_NAME`                   Nom de l'API            `DataFlow360 API`

  `APP_VERSION`                Version de              `0.1.0`
                               l'application           

  `ENVIRONMENT`                Environnement           `development`

  `CORS_ALLOWED_ORIGINS`       Origines autorisées du  `http://localhost:3000,http://localhost:5173`
                               frontend                

  `SIMULATION_ENABLED`         Active le mode          `true`
                               simulation, si          
                               applicable              

  `DATABASE_URL`               Connexion PostgreSQL    `postgresql+psycopg://...`

  `FRAUD_MODEL_PATH`           Chemin du modèle fraude `/app/models/fraude/modele_fraude_final.pkl`

  `FRAUD_DECISION_THRESHOLD`   Seuil de décision       `0.5`
                               fraude, si utilisé      

  `CREDIT_MODEL_PATH`          Chemin du modèle crédit `/app/models/credit/modele_scoring_credit_final.pkl`

  `CREDIT_MODEL_VERSION`       Version du modèle       `1.0`
                               crédit, si utilisée     

  `JWT_SECRET`                 Clé de signature JWT    à garder secrète

  `JWT_ALGORITHM`              Algorithme JWT          `HS256`

  `JWT_EXPIRES_MINUTES`        Durée de validité du    `1440`
                               token                   

  `KAFKA_HOST`                 Hôte Kafka interne      `kafka`

  `KAFKA_PORT`                 Port Kafka interne      `19092`

  `API_BASE_URL`               URL de l'API utilisée   `http://api:8000`
                               par le consumer         

  `SERVICE_EMAIL`              Compte technique du     `service-consumer@dataflow360.com`
                               consumer                

  `SERVICE_PASSWORD`           Mot de passe du compte  valeur locale à configurer
                               technique               
  -----------------------------------------------------------------------------------------------------------

Ne committe jamais `.env`, de mots de passe réels, de secrets JWT ou de
tokens.

## 5. Authentification JWT

Les routes protégées nécessitent un token JWT. Les routes publiques
documentées comprennent `/`, `/health` et `POST /auth/login`. Vérifie la
configuration réelle dans Swagger.

  Méthode   Route           Accès    Fonction
  --------- --------------- -------- -----------------------------------------
  `POST`    `/auth/login`   Public   Connexion avec formulaire
  `GET`     `/auth/me`      JWT      Informations sur l'utilisateur connecté
  `POST`    `/auth/users`   Admin    Créer un utilisateur
  `GET`     `/auth/users`   Admin    Lister les utilisateurs

La route `/auth/register` est indiquée comme supprimée dans la
documentation précédente ; les comptes sont alors créés par un
administrateur. Confirme ce comportement dans la version courante.

### Se connecter

``` bash
curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=<EMAIL>" \
  --data-urlencode "password=<MOT_DE_PASSE>"
```

La réponse doit contenir un `access_token` si l'authentification
réussit. Pour appeler une route protégée :

``` bash
curl -i http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Utilise uniquement les comptes de démonstration configurés localement.
Change les identifiants par défaut avant tout déploiement non local.

## 6. Endpoints

La liste ci-dessous reprend les routes documentées. **La présence réelle
de chaque route doit être confirmée dans Swagger**
(`http://127.0.0.1:8000/docs`) ou dans `/openapi.json`.

### Santé et authentification

  Méthode   Route           Fonction
  --------- --------------- -------------------------
  `GET`     `/`             Accueil
  `GET`     `/health`       Vérification de santé
  `POST`    `/auth/login`   Connexion
  `GET`     `/auth/me`      Utilisateur connecté
  `POST`    `/auth/users`   Créer un utilisateur
  `GET`     `/auth/users`   Lister les utilisateurs

### Clients

  ------------------------------------------------------------------------
  Méthode                 Route                    Fonction
  ----------------------- ------------------------ -----------------------
  `GET`                   `/clients`               Liste des clients, avec
                                                   pagination selon la
                                                   route

  `GET`                   `/clients/{client_id}`   Détail d'un client
  ------------------------------------------------------------------------

### Fraude

  ----------------------------------------------------------------------------
  Méthode                 Route                        Fonction
  ----------------------- ---------------------------- -----------------------
  `POST`                  `/fraud/predict`             Calcul du risque d'une
                                                       transaction

  `GET`                   `/fraud/alerts`              Liste des alertes

  `GET`                   `/fraud/alerts/{alert_id}`   Détail d'une alerte

  `PATCH`                 `/fraud/alerts/{alert_id}`   Mise à jour du
                                                       traitement d'une alerte

  `GET`                   `/fraud/stats`               Statistiques fraude
  ----------------------------------------------------------------------------

### Crédit

  -----------------------------------------------------------------------------------------
  Méthode                 Route                                     Fonction
  ----------------------- ----------------------------------------- -----------------------
  `POST`                  `/credit/score`                           Scoring manuel avec les
                                                                    15 variables

  `POST`                  `/credit/score/auto`                      Scoring à partir de
                                                                    l'historique, si la
                                                                    route est présente

  `GET`                   `/credit/score/{application_id}`          Dernier score d'une
                                                                    demande

  `GET`                   `/credit/applications`                    Liste des demandes de
                                                                    crédit

  `GET`                   `/credit/applications/{application_id}`   Détail d'une demande

  `GET`                   `/credit/stats`                           Statistiques crédit
  -----------------------------------------------------------------------------------------

## 7. Scoring de crédit

Le modèle documenté est `models/credit/modele_scoring_credit_final.pkl`.
Son intégration réelle a déjà été signalée comme fonctionnelle lors d'un
essai précédent : une requête a renvoyé `is_simulation: false`. Ce
parcours doit être retesté dans l'environnement actuel.

### Les 15 variables documentées

``` text
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

### Échelles et formules à confirmer

La documentation précédente indique que `regularite_revenus`,
`stabilite_flux` et `taux_remboursement` sont exprimés entre 0 et 100.
Toutefois, une requête de test antérieure utilisait des valeurs comme
`0.9` et `0.95`. **Cette incohérence doit être résolue en comparant les
données d'entraînement, le code de préparation des variables et le
contrat attendu par le modèle.**

Les formules exactes de `regularite_revenus` et `stabilite_flux` n'ont
pas encore été retrouvées dans le code consulté. Elles ne sont donc pas
affirmées dans ce README.

### Interprétation du score

Le comportement précédemment documenté était :

-   classe `1` : client éligible ;
-   `predict_proba(...)[0][1]` : probabilité associée à la classe 1 ;
-   seuil métier documenté : `0.90`.

``` text
score >= 0.90  -> eligible = true
score <  0.90  -> eligible = false
```

Le seuil de 90 % doit être confirmé par l'équipe Data Science avant
toute interprétation métier définitive. Le score reste une aide à la
décision et ne remplace pas l'analyse humaine.

Le champ `explanation_factors` a précédemment été observé à `null`. Ne
présente pas les facteurs explicatifs comme disponibles tant que leur
implémentation n'a pas été vérifiée.

### Scoring automatique

La route documentée `POST /credit/score/auto` prend quatre champs et
calcule les autres variables à partir de l'historique du client :

``` json
{
  "account_id": "CLI-000001",
  "montant_credit_demande": 200000,
  "duree_credit_demande": 6,
  "type_activite": "commerce"
}
```

Types d'activité documentés : `commerce`, `agriculture`, `transport`,
`services`. La route, les champs et les règles de calcul doivent être
confirmés dans la version actuelle de l'API.

### Scoring manuel

`POST /credit/score` est documenté comme un endpoint avancé qui reçoit
les 15 variables. Il est utile pour les tests du contrat du modèle.
Vérifie le schéma Pydantic courant dans Swagger avant de préparer une
requête.

## 8. Détection de fraude et Kafka

### Prédiction HTTP

`POST /fraud/predict` évalue le risque d'une transaction. L'intégration
du modèle réel de fraude avait été signalée comme fonctionnelle, mais
elle doit être retestée dans l'environnement courant.

Le traitement documenté est le suivant :

1.  validation des données ;
2.  préparation des variables attendues par le modèle ;
3.  prédiction ;
4.  calcul du score et du niveau de risque ;
5.  persistance en base selon la règle de traitement, documentée comme
    limitée aux alertes de niveau `high`.

Vérifie le champ `is_simulation` dans la réponse pour savoir si le
modèle réel a été utilisé.

### Pipeline Kafka

``` text
Producer -> topic transactions.raw -> Consumer
                                    |
                                    v
                           POST /fraud/predict
                                    |
                                    v
                              Modèle fraude
                                    |
                                    v
                    Persistance des alertes HIGH
```

Le comportement documenté est que le producer publie des transactions,
le consumer les lit et appelle l'API avec un JWT. La persistance des
alertes `high` doit être confirmée par les logs et par les données en
base.

### Alertes et statuts

Les statuts documentés sont :

-   `pending` : créée, non traitée ;
-   `reviewed` : examinée ;
-   `confirmed` : suspicion confirmée après analyse ;
-   `dismissed` : alerte écartée.

Les paramètres de pagination et les filtres réellement acceptés doivent
être confirmés dans Swagger.

### Statistiques fraude

Les champs documentés de `GET /fraud/stats` comprennent :

  -----------------------------------------------------------------------
  Champ                               Signification documentée
  ----------------------------------- -----------------------------------
  `total_transactions`                Nombre total de transactions

  `total_alerts`                      Nombre total d'alertes

  `suspicious_rate`                   Ratio alertes / transactions, selon
                                      l'implémentation

  `suspicious_amount`                 Montant des transactions alertées

  `alerts_by_status`                  Répartition par statut

  `alerts_by_risk_level`              Répartition par niveau de risque

  `alerts_evolution`                  Évolution quotidienne
  -----------------------------------------------------------------------

Ces noms et calculs doivent être vérifiés sur la réponse actuelle de
l'API.

## 9. Base de données

Les six tables documentées sont :

-   `api_users`
-   `api_clients`
-   `api_transactions`
-   `api_fraud_alerts`
-   `api_credit_applications`
-   `api_credit_scores`

Les noms et colonnes exacts doivent correspondre à `api/db/models.py` et
aux migrations réellement exécutées. Les données de démonstration sont
synthétiques et ne représentent pas de vrais clients.

## 10. Tests du backend et état des vérifications

Cette section distingue les vérifications déjà rapportées des contrôles
qui restent nécessaires. Elle ne signifie pas que toute la suite
automatisée a réussi.

### État au 9 octobre 2026

  -------------------------------------------------------------------------
  Élément                 État                    Détail
  ----------------------- ----------------------- -------------------------
  Chargement du modèle    **Vérifié               Le modèle réel avait été
  crédit                  précédemment**          chargé avec succès dans
                                                  le conteneur lors d'un
                                                  test antérieur.

  `POST /credit/score`    **Vérifié               Une réponse de test avait
  avec modèle réel        précédemment**          renvoyé un score et
                                                  `is_simulation: false`.

  Intégration du modèle   **Vérifiée              L'intégration au modèle
  fraude                  précédemment, à         réel avait été signalée
                          retester**              comme fonctionnelle.

  Démarrage actuel de     **À confirmer**         Une sortie partielle
  tous les conteneurs                             montrait
                                                  `dataflow360-db-init` en
                                                  état `Exited`, ce qui
                                                  peut être normal pour un
                                                  service d'initialisation.
                                                  Il faut examiner l'état
                                                  de sortie et les logs.

  `GET /health` dans      **Non confirmé**        La sortie partagée ne
  l'environnement courant                         permettait pas de lire
                                                  clairement le statut HTTP
                                                  et le corps de réponse.

  `GET /openapi.json`     **Non confirmé**        Aucune sortie exploitable
                                                  n'avait été partagée.

  Liste actuelle des      **À tester**            L'extraction des routes
  routes OpenAPI                                  n'a pas donné de résultat
                                                  exploitable.

  Authentification JWT    **À retester**          Les routes sont
                                                  documentées, mais aucun
                                                  résultat de connexion
                                                  récent n'a été fourni
                                                  dans cette séquence.

  Routes clients, alertes **À tester**            Les réponses HTTP
  et statistiques                                 actuelles ne sont pas
                                                  encore confirmées.

  Pipeline Kafka de bout  **À tester**            Vérifier les logs du
  en bout                                         producer et du consumer,
                                                  puis l'apparition de
                                                  nouvelles alertes.

  Suite automatisée       **À tester**            Aucun résultat récent de
  complète                                        la commande de tests n'a
                                                  été fourni.
  -------------------------------------------------------------------------

### Étape A --- Vérifier les conteneurs

``` bash
cd ~/Projet-Dataflow360
docker compose ps -a
```

### Étape B --- Vérifier les réponses HTTP

``` bash
curl -i --max-time 5 http://127.0.0.1:8000/health
curl -i --max-time 5 http://127.0.0.1:8000/openapi.json
```

Cherche un statut HTTP explicite, par exemple `200 OK`, et un corps JSON
lisible. Si la commande échoue, conserve le message d'erreur complet.

Pour afficher les routes si `/openapi.json` renvoie du JSON valide :

``` bash
curl -fsS --max-time 5 http://127.0.0.1:8000/openapi.json \
  | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['paths'].keys()))"
```

### Étape C --- Examiner les logs de l'API

``` bash
docker compose logs --tail=100 api
```

### Étape D --- Exécuter les tests automatisés

La commande documentée dans le projet est :

``` bash
docker compose --profile test run --rm api-tests
```

Confirme que le service `api-tests` existe dans le `docker-compose.yml`.
Conserve le code de sortie et le résumé final (`passed`, `failed`,
erreurs éventuelles). La suite ne doit être déclarée validée qu'après un
résultat réussi.

### Étape E --- Tester l'authentification et les routes protégées

1.  Se connecter via `POST /auth/login`.
2.  Récupérer l'`access_token`.
3.  Appeler `/auth/me` avec `Authorization: Bearer <ACCESS_TOKEN>`.
4.  Tester les routes clients, crédit et fraude dans Swagger.
5.  Vérifier les statuts HTTP, les schémas de réponse et la persistance
    attendue en base.

### Étape F --- Tester Kafka de bout en bout

``` bash
docker compose logs --tail=100 transaction-producer
docker compose logs --tail=100 fraud-consumer
```

Vérifie que les services sont actifs, que le consumer reçoit des
messages et que l'API accepte les requêtes. Pour confirmer la
persistance, compare les alertes en base avant et après le test, en
tenant compte de la règle de persistance effectivement implémentée.

## 11. Frontend

Le frontend se trouve dans `frontend/`. Exemple de configuration :

``` dotenv
VITE_API_BASE_URL=http://localhost:8000
```

L'origine du frontend doit être autorisée dans la configuration CORS de
l'API. Vérifie les valeurs effectives dans `.env` et
`api/core/config.py`.

Points d'intégration à tester côté frontend :

-   connexion et gestion du JWT ;
-   envoi du header `Authorization: Bearer <token>` ;
-   gestion des réponses `401`, `403`, `422` et `5xx` ;
-   pagination et filtres des listes ;
-   distinction entre réponse simulée et résultat du modèle via
    `is_simulation` ;
-   interprétation du champ `eligible` ;
-   actualisation périodique des alertes, si le polling est utilisé.

Le frontend ne doit pas être considéré comme la cause d'une erreur tant
que les routes de l'API n'ont pas été testées directement avec `curl` ou
Swagger.

## 12. Limites et prochaines étapes

-   Les données du projet sont synthétiques.
-   Le seuil d'éligibilité crédit de `0.90` reste à valider par l'équipe
    Data Science.
-   Les formules exactes de `regularite_revenus` et `stabilite_flux`
    doivent être retrouvées dans le code et documentées.
-   Les échelles des variables de régularité et de stabilité doivent
    être clarifiées en comparant le code d'entraînement et les données.
-   Les facteurs d'explicabilité du crédit ne doivent pas être inventés
    ; vérifier l'état de `explanation_factors` et de toute intégration
    SHAP.
-   Le fonctionnement de toutes les routes et du pipeline Kafka doit
    être confirmé par des tests reproductibles.
-   Les scores de seed sont indiqués dans la documentation précédente
    comme fictifs ; ne pas les présenter comme des prédictions du modèle
    réel sans vérification.
-   Le README doit être mis à jour après toute modification de route, de
    schéma, de configuration ou de test.

## Bonnes pratiques de développement

Lorsqu'une fonctionnalité évolue, vérifier et mettre à jour selon le
besoin :

1.  le schéma Pydantic ;
2.  le service métier ;
3.  le repository ;
4.  la route ;
5.  les tests ;
6.  la documentation Swagger ;
7.  les logs et la gestion des erreurs ;
8.  ce README.

La séparation attendue des responsabilités est :

``` text
Router -> Service -> Repository -> Database
```

Le modèle ML doit rester séparé de la route HTTP.

## Principe métier à respecter

``` text
Données -> Analyse -> Modèle ML -> Score de risque
                                      |
                                      v
                              Information analyste
                                      |
                                      v
                                Décision humaine
```

Le système ne doit pas :

-   bloquer automatiquement une transaction ;
-   accuser juridiquement un client ;
-   accorder automatiquement un crédit ;
-   refuser automatiquement un crédit.

Les décisions finales restent humaines.
