# SenTerangaSafe Frontend — Docker + hot reload

- **UI** : http://localhost:3000 (Vite, rechargement auto)
- **API** : http://localhost:8000

Toute modification dans `frontend/src/**` est prise en compte **immédiatement**.

## Fichiers Docker

| Fichier | Emplacement | Rôle |
|---------|-------------|------|
| `Dockerfile.dev` | `frontend/` | Image Node + Vite |
| `docker-compose.override.yml` | **racine** projet | Force frontend en mode HMR |
| `.env` | racine | `VITE_API_BASE_URL`, ports, CORS |

## Variables utiles (racine `.env`)

```env
VITE_API_BASE_URL=http://localhost:8000
FRONTEND_PORT=3000
API_PORT=8000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SIMULATION_ENABLED=true
```

## Compte


