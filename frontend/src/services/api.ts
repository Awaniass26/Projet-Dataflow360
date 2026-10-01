/**
 * Instance Axios centrale
 * Tous les appels API passent par ici.
 *
 * Quand le backend FastAPI sera prêt :
 * - Remplace simplement les mocks dans les services
 * - L'intercepteur JWT gère déjà l'authentification
 */

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

/**
 * Intercepteur de requête : ajoute le token JWT s'il existe
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Intercepteur de réponse : gestion globale des erreurs
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expiré ou invalide → on déconnecte
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
