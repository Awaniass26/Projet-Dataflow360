# DataFlow360 — Frontend

Interface utilisateur de la plateforme **DataFlow360** : système intelligent de Scoring Crédit et de détection de fraude pour les fintechs Mobile Money.

Ce frontend consomme exclusivement l’API backend développée avec **FastAPI**.

---

## Stack technique

| Couche              | Technologie                  | Rôle |
|---------------------|------------------------------|------|
| Framework           | React 19 + TypeScript        | Application SPA |
| Build tool          | Vite                         | Développement et build ultra-rapide |
| Styling             | Tailwind CSS + shadcn/ui     | Design system moderne et accessible |
| Data fetching       | TanStack Query               | Cache, loading states, gestion d’erreurs API |
| Graphiques          | Recharts                     | Visualisation des KPI et scores |
| Tableaux            | TanStack Table               | Affichage des transactions, clients, alertes |
| Routing             | React Router                 | Navigation entre les pages |
| HTTP Client         | Axios                        | Appels vers l’API FastAPI |

---

## Prérequis

- Node.js ≥ 20
- npm ou pnpm
- L’API FastAPI doit être démarrée (par défaut sur `http://localhost:8000`)

---

## Installation

```bash
# Cloner le dépôt (ou se placer dans le dossier frontend)
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

L’application sera accessible sur : [http://localhost:5173](http://localhost:5173)

---

## Configuration

Créer un fichier `.env` à la racine du frontend :

```env
VITE_API_BASE_URL=http://localhost:8000
```

> En production, cette variable pointe vers l’URL publique de l’API FastAPI.

---

## Scripts disponibles

| Commande          | Description                          |
|-------------------|--------------------------------------|
| `npm run dev`     | Lance le serveur de développement    |
| `npm run build`   | Génère le build de production        |
| `npm run preview` | Prévisualise le build de production  |
| `npm run lint`    | Vérifie le code avec ESLint          |

---

## Structure du projet

```
frontend/
├── public/                 # Assets statiques
├── src/
│   ├── components/         # Composants réutilisables
│   │   ├── ui/             # Composants shadcn/ui
│   │   ├── charts/         # Graphiques (Recharts)
│   │   ├── tables/         # Tableaux de données
│   │   └── layout/         # Header, Sidebar, Layout
│   ├── features/           # Fonctionnalités métier
│   │   ├── dashboard/      # Vue d’ensemble KPI
│   │   ├── credit-scoring/ # Scoring crédit
│   │   ├── fraud/          # Alertes et détection de fraude
│   │   └── clients/        # Fiches clients
│   ├── hooks/              # Custom hooks
│   ├── services/           # Appels API (Axios)
│   ├── types/              # Types TypeScript
│   ├── lib/                # Utilitaires
│   ├── App.tsx
│   └── main.tsx
├── .env
├── Dockerfile
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

---

## Connexion à l’API FastAPI

Tous les appels API passent par TanStack Query + Axios.

Exemple de service :

```ts
// src/services/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Intercepteur pour ajouter le token JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

---

## Docker

### Build de l’image

```bash
docker build -t dataflow360-frontend .
```

### Lancer le conteneur

```bash
docker run -d \
  -p 3000:80 \
  -e VITE_API_BASE_URL=http://votre-api:8000 \
  --name dataflow360-frontend \
  dataflow360-frontend
```

L’application sera accessible sur : [http://localhost:3000](http://localhost:3000)

> Le Dockerfile utilise un build multi-stage (Node pour le build + Nginx pour servir les fichiers statiques).



