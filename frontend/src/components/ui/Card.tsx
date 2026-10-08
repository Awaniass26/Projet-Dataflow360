import { cn } from "@/lib/utils";

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-100/80 bg-white p-5 shadow-card",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p className={cn("text-xs font-medium uppercase tracking-wide text-slate-500", className)}>
      {children}
    </p>
  );
}

export function CardValue({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p className={cn("mt-2 text-2xl font-bold tracking-tight text-slate-900", className)}>
      {children}
    </p>
  );
}

/**
 * KPI card avec 3 tirets verticaux aux couleurs du logo (bleu / or / vert)
 */
export function KpiCard({
  title,
  value,
  hint,
  accent = "blue",
}: {
  title: string;
  value: React.ReactNode;
  hint?: string;
  accent?: "blue" | "gold" | "green" | "danger";
}) {
  const valueColor =
    accent === "danger"
      ? "text-danger"
      : accent === "gold"
        ? "text-brand-gold"
        : accent === "green"
          ? "text-brand-green"
          : "text-slate-900";

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-100/80 bg-white shadow-card">
      {/* 3 tirets verticaux — charte logo */}
      <div className="absolute inset-y-0 left-0 flex w-[6px]">
        <span className="h-full w-[2px] bg-brand-blue" />
        <span className="h-full w-[2px] bg-brand-gold" />
        <span className="h-full w-[2px] bg-brand-green" />
      </div>

      <div className="pl-5 pr-5 py-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {title}
        </p>
        <p className={cn("mt-2 text-2xl font-bold tracking-tight", valueColor)}>
          {value}
        </p>
        {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
      </div>
    </div>
  );
}
