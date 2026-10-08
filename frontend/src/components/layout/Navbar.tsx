import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  ShieldAlert,
  FileText,
  UserPlus,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { getStoredUser, isAdmin, logout } from "@/services/auth";
import { ROLE_LABELS } from "@/lib/labels";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Clients", href: "/clients", icon: Users },
  { name: "Scoring", href: "/scoring", icon: FileText },
  { name: "Alertes Fraude", href: "/fraud", icon: ShieldAlert },
];

export function Navbar() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const admin = isAdmin();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 shadow-nav backdrop-blur-md">
      <div className="flex h-16 w-full items-center gap-4 px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <NavLink to="/" className="flex shrink-0 items-center gap-3">
          <img
            src="/logo-senterangasafe.jpeg"
            alt="SenTerangaSafe"
            className="h-10 w-10 rounded-full object-cover ring-2 ring-brand-blue/10"
          />
          <div className="hidden sm:block">
            <p className="text-sm font-bold leading-tight tracking-tight">
              <span className="text-brand-blue">Sen</span>
              <span className="text-brand-gold">Teranga</span>
              <span className="text-brand-green">Safe</span>
            </p>
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              Mobile Money Risk
            </p>
          </div>
        </NavLink>

        {/* Desktop nav */}
        <nav className="ml-4 hidden flex-1 items-center justify-center gap-1 md:flex">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              end={item.href === "/"}
              className={({ isActive }) =>
                cn(
                  "inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-brand-blue-soft text-brand-blue"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </NavLink>
          ))}

          {admin && (
            <NavLink
              to="/users"
              className={({ isActive }) =>
                cn(
                  "inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-brand-gold-soft text-brand-gold"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )
              }
            >
              <UserPlus className="h-4 w-4" />
              Utilisateurs
            </NavLink>
          )}
        </nav>

        {/* User + logout */}
        <div className="hidden items-center gap-3 md:flex">
          {user && (
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-800">
                {user.full_name}
              </p>
              <p className="text-[11px] text-slate-400">
                {ROLE_LABELS[user.role] ?? user.role}
              </p>
            </div>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
          >
            <LogOut className="h-4 w-4" />
            Déconnexion
          </button>
        </div>

        {/* Mobile toggle */}
        <button
          type="button"
          className="ml-auto rounded-xl p-2 text-slate-600 hover:bg-slate-50 md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="border-t border-slate-100 bg-white px-4 py-3 md:hidden">
          <nav className="flex flex-col gap-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                end={item.href === "/"}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "inline-flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium",
                    isActive
                      ? "bg-brand-blue-soft text-brand-blue"
                      : "text-slate-600 hover:bg-slate-50"
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </NavLink>
            ))}
            {admin && (
              <NavLink
                to="/users"
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "inline-flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium",
                    isActive
                      ? "bg-brand-gold-soft text-brand-gold"
                      : "text-slate-600 hover:bg-slate-50"
                  )
                }
              >
                <UserPlus className="h-4 w-4" />
                Utilisateurs
              </NavLink>
            )}
            <button
              type="button"
              onClick={handleLogout}
              className="mt-2 inline-flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4" />
              Déconnexion
            </button>
          </nav>
        </div>
      )}
    </header>
  );
}
