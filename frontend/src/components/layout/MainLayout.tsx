/**
 * Layout principal : Sidebar + Header barre top + contenu
 */

import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";

export function MainLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />

      {/* Barre d'en-tête fixe Dataflow */}
      <header className="fixed top-0 left-64 right-0 z-20 flex h-16 items-center border-b border-gray-200 bg-white px-6">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-900">SenTerangaSafe</span>
          <span className="text-gray-300">|</span>
          <span className="text-sm text-gray-500">Scoring Crédit & Détection de Fraude</span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
            Mode démo
          </span>
        </div>
      </header>

      {/* Contenu principal */}
      <main className="pl-64 pt-16">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
