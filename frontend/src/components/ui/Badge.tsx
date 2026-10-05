/**
 * Badge de niveau de risque / statut d'alerte
 */

import { cn } from "@/lib/utils";
import type { FraudStatus, RiskLevel } from "@/types/fraud";

const riskStyles: Record<RiskLevel, string> = {
  low: "bg-green-50 text-green-700 ring-green-600/20",
  medium: "bg-orange-50 text-orange-700 ring-orange-600/20",
  high: "bg-red-50 text-red-700 ring-red-600/20",
};

const statusStyles: Record<FraudStatus, string> = {
  pending: "bg-orange-50 text-orange-700 ring-orange-600/20",
  reviewed: "bg-blue-50 text-blue-700 ring-blue-600/20",
  confirmed: "bg-red-50 text-red-700 ring-red-600/20",
  dismissed: "bg-gray-100 text-gray-600 ring-gray-500/20",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: "risk" | "status" | "default";
  value?: string;
  className?: string;
}

export function Badge({ children, variant = "default", value, className }: BadgeProps) {
  let styles = "bg-gray-50 text-gray-700 ring-gray-600/20";

  if (variant === "risk" && value) {
    styles = riskStyles[value as RiskLevel] ?? styles;
  }
  if (variant === "status" && value) {
    styles = statusStyles[value as FraudStatus] ?? styles;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        styles,
        className
      )}
    >
      {children}
    </span>
  );
}