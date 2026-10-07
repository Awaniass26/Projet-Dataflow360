import { cn } from "@/lib/utils";

const variants: Record<string, string> = {
  default: "bg-slate-100 text-slate-700",
  blue: "bg-brand-blue-soft text-brand-blue",
  gold: "bg-brand-gold-soft text-brand-gold",
  green: "bg-brand-green-soft text-brand-green",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-red-700",
};

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: keyof typeof variants;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        variants[variant] ?? variants.default,
        className
      )}
    >
      {children}
    </span>
  );
}
