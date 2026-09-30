
# Projet-Dataflow360

> Plateforme intelligente de détection de fraude et d'évaluation du risque de crédit dans les services de mobile money au Sénégal.

---

## Présentation

**DataFlow360** est un projet de FinTech qui vise à exploiter les données issues du mobile money afin d'améliorer la gestion des risques financiers.

Le projet répond à deux problématiques principales :

- 🔴 **Détection de fraude** : identifier les transactions présentant un comportement suspect et calculer un score de risque.
- 🟡 **Credit Scoring** : évaluer le risque de défaut d'un client à partir de son comportement financier et de son historique.

L'objectif est de mettre en place une solution permettant de **générer, collecter, contrôler, transformer, analyser et exploiter les données** afin d'aider à la prise de décision.

> Toutes les données utilisées dans ce projet sont **synthétiques** et sont générées avec **Faker en Python** à des fins pédagogiques et de prototypage. Elles ne représentent pas des données réelles de clients sénégalais.

---

## 2. Objectifs

### Détection de fraude

- Générer des transactions de mobile money.
- Analyser les comportements transactionnels.
- Détecter les comportements inhabituels ou suspects.
- Calculer un score de risque de fraude.
- Générer des alertes pour les transactions à risque élevé.
- Fournir une explication des alertes.
- Suivre les cas de fraude détectés.

### Credit Scoring

- Générer les profils clients et leurs historiques financiers.
- Analyser les habitudes de transaction.
- Créer des variables comportementales.
- Évaluer le risque de défaut.
- Générer un score de crédit.
- Identifier les facteurs contribuant au score.
- Historiser les scores.

---

## 3. Données

Le projet peut s'appuyer sur plusieurs types de données :

- Transactions mobile money
- Données clients
- Historique des crédits
- Historique des remboursements
- Données comportementales
- Données synthétiques pour le prototypage et les tests

> Les données synthétiques sont utilisées à des fins pédagogiques et de démonstration. Elles ne remplacent pas des données réelles de production.

### Exemples de variables

#### Transactions
- Identifiant de transaction
- Identifiant client
- Date et heure
- Type de transaction
- Montant
- Solde avant/après transaction
- Canal de transaction
- Destinataire
- Localisation
- Statut

#### Clients
- Identifiant client
- Âge
- Région
- Type de compte
- Ancienneté du compte
- Fréquence d'utilisation

#### Crédits
- Identifiant du crédit
- Identifiant client
- Montant demandé
- Durée du crédit
- Revenus estimés
- Dépenses
- Historique de remboursement
- Retards de paiement
- Statut du crédit

## 4. Pipeline de traitement des données

Le pipeline suit généralement le schéma suivant :

```text
Collecte des données
    -> Stockage
    -> Contrôle qualité
    -> Transformation
    -> Feature engineering
    -> Modélisation
    -> Analyse et exploitation
    -> Décision / alertes
```

## 5. Architecture du projet

Le projet est structuré pour séparer les responsabilités suivantes : gestion des données, analyse exploratoire, modélisation, API, streaming, tableau de bord et tests.

```text
DataFlow360/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── requirements.txt
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── notebooks/
│   ├── eda_fraude.ipynb
│   └── eda_credit.ipynb
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   │   ├── fraud/
│   │   └── credit/
│   └── utils/
├── api/
│   ├── main.py
│   ├── routers/
│   │   ├── fraud.py
│   │   └── credit.py
│   └── schemas/
├── streaming/
│   ├── producer.py
│   └── consumer.py
├── dashboard/
│   ├── app.py
│   ├── pages/
│   │   ├── fraude.py
│   │   └── credit.py
│   └── components/
├── models_store/
├── tests/
│   ├── test_data.py
│   ├── test_api.py
│   └── test_models.py
├── docs/
└── .github/
```

## 6. Description des composants

### data/
Le dossier de données contient les jeux de données bruts, transformés et synthétiques utilisés pour l'analyse et la modélisation.

- raw/ : données brutes non altérées
- processed/ : données nettoyées et préparées
- synthetic/ : données générées pour le prototypage et la démonstration

### notebooks/
Contient les analyses exploratoires et les expériences de modélisation.

### src/
Le cœur du projet, où sont implémentés les traitements, le feature engineering et les modèles de machine learning.

- data/ : ingestion, nettoyage et préparation des données
- features/ : création de variables utiles à la modélisation
- models/ : entraînement, validation et sauvegarde des modèles
- utils/ : fonctions utilitaires et outils partagés

### api/
Contient l'API backend exposant les services métier du projet.

- main.py : point d'entrée de l'application
- routers/ : routes des services liés à la fraude et au scoring
- schemas/ : modèles de validation et de structuration des entrées/sorties

### streaming/
Contient les composants de traitement en flux, notamment le producteur et le consommateur de messages.

### dashboard/
Regroupe les interfaces de visualisation et de supervision du projet.

### tests/
Contient les tests de validation des données, de l'API et des modèles.

## 7. Exemple de flux métier

```text
Transaction
    -> Producer
    -> Kafka
    -> Consumer
    -> Modèle de fraude
    -> Score de risque
    -> Alerte / action
```

## 8. Prérequis

Avant de lancer le projet, il est nécessaire d'avoir :

- Python 3.10 ou supérieur
- pip ou un gestionnaire d'environnement virtuel
- Docker et Docker Compose pour les services conteneurisés
- Accès à un environnement d'exécution compatible avec les dépendances du projet

## 9. Installation

1. Cloner le dépôt.
2. Créer un environnement virtuel.
3. Installer les dépendances.
4. Vérifier la configuration des variables d'environnement.
5. Lancer les services ou l'API selon le cas d'usage.

Exemple :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 10. Utilisation

Le projet peut être utilisé de plusieurs manières :

- Exécution de l'API pour exposer des prédictions
- Analyse des données via notebooks
- Lancement du dashboard pour visualiser les résultats
- Traitement des événements en temps réel via streaming
- Validation avec les tests automatisés

## 11. Tests

Les tests du projet sont organisés pour valider les fonctions critiques sur :

- les données
- l'API
- les modèles

Commande typique :

```bash
pytest
```

## 12. Évolution du projet

Les prochaines étapes peuvent inclure :

- amélioration des modèles de détection de fraude
- ajout de métriques business et de monitoring
- mise en place d'un pipeline MLOps plus robuste
- intégration de données temps réel
- préparation d'une version production avec sécurité et traçabilité

## 13. Licence

Ce projet est fourni à des fins de démonstration et de prototypage. La licence exacte doit être confirmée selon le contexte de déploiement et les droits d'utilisation du projet.

## 14. Résumé

DataFlow360 a pour objectif de fournir une base solide pour la gestion intelligente du risque financier dans un environnement mobile money, avec une combinaison de données, d'analyse, de modélisation et d'outils décisionnels.


Contient le dashboard développé avec Dash + Plotly.

dashboard/
├── app.py
├── pages/
│   ├── fraude.py
│   └── credit.py
└── components/
app.py

Point d'entrée de l'application Dashboard.

pages/

Contient les différentes pages du dashboard.

fraude.py

Interface de suivi de la fraude.

Elle peut notamment afficher :

nombre de transactions ;
nombre d'alertes ;
taux de fraude ;
montants suspects ;
évolution des alertes ;
niveaux de risque ;
transactions à risque.
credit.py

Interface dédiée au credit scoring.

Elle peut notamment afficher :

nombre de demandes ;
montant moyen ;
score moyen ;
profils de risque ;
taux de défaut ;
évolution des demandes.
components/

Contient les composants réutilisables du dashboard :

graphiques ;
cartes KPI ;
filtres ;
tableaux ;
éléments d'interface.
📂 models_store/

Contient les modèles de Machine Learning entraînés et sauvegardés.

Exemples :

models_store/
├── fraud_model.pkl
└── credit_model.pkl

Les modèles peuvent être sauvegardés au format .pkl ou .joblib.

⚠️ Les fichiers de modèles volumineux ne doivent pas nécessairement être versionnés dans Git. Ils peuvent être ajoutés au .gitignore.

📂 tests/

Contient les tests automatisés du projet.

tests/
├── test_data.py
├── test_api.py
└── test_models.py
test_data.py

Teste les traitements et contrôles liés aux données.

test_api.py

Teste les endpoints et comportements de l'API.

test_models.py

Teste les modèles et leurs fonctions de prédiction.

📂 docs/

Contient la documentation et les livrables du projet.

On peut notamment y retrouver :

documentation du cadrage ;
besoins fonctionnels ;
cycle de vie des données ;
architecture ;
diagrammes ;
conception ;
choix technologiques ;
organisation de l'équipe ;
documentation technique ;
supports de présentation.
🔄 Circulation globale des données

La circulation des données dans DataFlow360 peut être représentée de manière simplifiée comme suit :

                    SOURCES DE DONNÉES
                           │
                           ▼
              ┌────────────────────────┐
              │      Acquisition       │
              │   Batch / Streaming    │
              └───────────┬────────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       Données brutes            Kafka Streaming
       data/raw/                      │
             │                        ▼
             │                 Détection fraude
             │                        │
             ▼                        ▼
       Contrôle qualité          Score de risque
             │                        │
             ▼                        ▼
       Transformation              Alerte
             │
             ▼
       Feature Engineering
             │
       ┌─────┴─────┐
       ▼           ▼
    Modèle       Modèle
    Fraude       Crédit
       │           │
       └─────┬─────┘
             ▼
          FastAPI
             │
             ▼
       Dash + Plotly
             │
             ▼
      Analyse / Décision
🔗 Interaction entre les composants

Les principaux composants du projet communiquent de la manière suivante :

Data
 ↓
Data Engineering
 ↓
Feature Engineering
 ↓
Machine Learning
 ↓
FastAPI
 ↓
Dashboard

Pour la détection de fraude, Kafka intervient dans le flux :

Transaction
 ↓
Kafka
 ↓
Modèle de fraude
 ↓
FastAPI
 ↓
Dashboard / Alerte

Pour les traitements batch et le réentraînement des modèles, Airflow intervient dans l'orchestration :

Collecte
 ↓
Qualité
 ↓
Transformation
 ↓
Feature Engineering
 ↓
Entraînement
 ↓
Évaluation
 ↓
Mise à jour du modèle

### Et oui, je ferais **exactement cette distinction**

Dans le README, tu as :

1. **Présentation** → c'est quoi DataFlow360 ?
2. **Objectifs** → quels problèmes vous résolvez ?
3. **Données** → quelles données ?
4. **Architecture** → comment le projet est organisé ?
5. **Description de chaque dossier** → qui contient quoi ?
6. **Circulation des données** → comment les composants communiquent ?
7. **Technologies** → pourquoi elles sont là ?
8. **Installation** → comment lancer le projet ?
9. **Équipe** → qui fait quoi ?
10. **Git/GitHub** → comment vous collaborez ?

Comme ça, **le README devient aussi une documentation technique de référence pour les 5 membres**. Quand quelqu'un se demande *« je mets mon fichier où ? »*, il regarde le README et la réponse est claire.

# 6. Le fonctionnement Git/GitHub conseillé

Chaque personne travaille sur sa propre branche (`feature/eda`, `feature/ml`,
`feature/backend`, etc.). La branche `main` contient uniquement le code validé.

Avant de commencer :

```bash
git checkout main
git pull
git checkout TA_BRANCHE
git merge main
```

Après le développement et les tests :

```bash
git add .
git commit -m "feat: description du changement"
git push -u origin TA_BRANCHE
```

Ensuite, ouvrir une **Pull Request*Tâches* vers `main`. Après validation et fusion,
les autres membres récupèrent la nouvelle version avec la même procédure.

Ainsi, tout le monde commence son travail avec la dernière version validée de
`main`, que la branche concerne l'EDA, le ML, le backend ou le dashboard.

---

# 9. Et surtout : ne mettez PAS chacun vos codes n'importe où 😭

Par exemple le ML ne devrait pas créer :

```
awa_ml.py
test_ml_final.py
nouveau_ml.py
model2.py
```

à la racine du projet.

Il doit respecter l'architecture :

```
src/
└── models/
    ├── fraud/
    │   ├── train.py
    │   ├── predict.py
    │   └── ...
    │
    └── credit/
      ├── train.py
      ├── predict.py
      └── ...
```

C'est justement **l'architecture commune** qui permet à 5 personnes de travailler ensemble sans transformer le projet en chaos. 😂

