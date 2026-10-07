import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";

export function MainLayout() {
  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200/60 py-6">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 px-4 text-center sm:flex-row sm:text-left sm:px-6 lg:px-8">
          <p className="text-xs text-slate-400">
            © {new Date().getFullYear()} SenTerangaSafe — Plateforme de détection
            de fraudes & scoring de crédit Mobile Money
          </p>
          <p className="text-[11px] text-slate-300">
            Données synthétiques · Aide à la décision
          </p>
        </div>
      </footer>
    </div>
  );
}
