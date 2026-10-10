import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Activity, Shield, Database, Cpu } from "lucide-react";

export function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="min-h-[calc(100vh-4rem)] w-full flex-1 px-4 py-8 sm:px-6 lg:px-10">
        <Outlet />
      </main>

      {/* Footer professionnel SenTerangaSafe */}
      <footer className="relative mt-auto overflow-hidden border-t border-slate-200/80 bg-gradient-to-br from-slate-900 via-[#0f1f3d] to-slate-900 text-slate-300">
        {/* Décoration : lignes de marque */}
        <div className="absolute inset-x-0 top-0 flex h-1">
          <div className="h-full flex-1 bg-brand-blue" />
          <div className="h-full flex-1 bg-brand-gold" />
          <div className="h-full flex-1 bg-brand-green" />
        </div>

        <div className="relative mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {/* Colonne marque */}
            <div>
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-blue/20 ring-1 ring-brand-blue/40">
                  <Shield className="h-5 w-5 text-brand-gold" />
                </div>
                <div>
                  <p className="text-sm font-bold tracking-wide text-white">
                    SenTerangaSafe
                  </p>
                  <p className="text-[10px] uppercase tracking-widest text-brand-gold">
                    DataFlow360
                  </p>
                </div>
              </div>
              <p className="mt-3 max-w-xs text-xs leading-relaxed text-slate-400">
                Plateforme décisionnelle de détection de fraudes et de scoring
                de crédit pour le Mobile Money au Sénégal. Les scores sont des
                aides à la décision, jamais des décisions automatiques.
              </p>
            </div>

            {/* Colonne modules */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Modules
              </p>
              <ul className="mt-3 space-y-2 text-xs">
                <li className="flex items-center gap-2">
                  <Activity className="h-3.5 w-3.5 text-brand-green" />
                  Dashboard temps réel
                </li>
                <li className="flex items-center gap-2">
                  <Shield className="h-3.5 w-3.5 text-brand-gold" />
                  Détection fraude (ML)
                </li>
                <li className="flex items-center gap-2">
                  <Cpu className="h-3.5 w-3.5 text-brand-blue" />
                  Scoring crédit
                </li>
                <li className="flex items-center gap-2">
                  <Database className="h-3.5 w-3.5 text-slate-400" />
                  Clients &amp; alertes
                </li>
              </ul>
            </div>

            {/* Colonne statut pipeline */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Pipeline live
              </p>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                  <span>Kafka · Producer</span>
                  <span className="flex items-center gap-1.5 text-brand-green">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-green" />
                    actif
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                  <span>Consumer → API fraude</span>
                  <span className="flex items-center gap-1.5 text-brand-green">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-green" />
                    scoring
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                  <span>PostgreSQL · Alertes HIGH</span>
                  <span className="flex items-center gap-1.5 text-brand-gold">
                    <span className="h-1.5 w-1.5 rounded-full bg-brand-gold" />
                    persisté
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 flex flex-col items-center justify-between gap-3 border-t border-white/10 pt-6 text-center sm:flex-row sm:text-left">
            <p className="text-[11px] text-slate-500">
              © {new Date().getFullYear()} SenTerangaSafe — DataFlow360 · Projet
              académique · Données synthétiques
            </p>
            <p className="text-[11px] text-slate-600">
              Aide à la décision · Pas de décision automatique
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
