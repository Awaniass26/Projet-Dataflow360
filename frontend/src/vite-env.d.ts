/// <reference types="vite/client" />

/**
 * Déclarations de types pour Vite
 * - Permet d'importer des fichiers CSS
 * - Permet d'utiliser import.meta.env
 */

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
