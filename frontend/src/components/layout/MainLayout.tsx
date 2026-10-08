import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";

export function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="min-h-[calc(100vh-4rem)] w-full px-4 py-8 sm:px-6 lg:px-10">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200/60 py-6">
        <div className="flex w-full flex-col items-center justify-between gap-2 px-3 text-center sm:flex-row sm:text-left sm:px-4 lg:px-6">
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
