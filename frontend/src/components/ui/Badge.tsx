/**
 * Badge de statut / risque
 */

import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types/client";
import type { FraudSeverity } from "@/types/fraud";

const riskStyles: Record<RiskLevel, string> = {
  faible: "bg-green-50 text-green-700 ring-green-600/20",
  moyen: "bg-orange-50 text-orange-700 ring-orange-600/20",
  élevé: "bg-red-50 text-red-700 ring-red-600/20",
};

const severityStyles: Record<FraudSeverity, string> = {
  basse: "bg-blue-50 text-blue-700 ring-blue-600/20",
  moyenne: "bg-orange-50 text-orange-700 ring-orange-600/20",
  haute: "bg-red-50 text-red-700 ring-red-600/20",
  critique: "bg-red-100 text-red-800 ring-red-600/30 font-semibold",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: "risk" | "severity" | "default";
  value?: string;
  className?: string;
}

export function Badge({ children, variant = "default", value, className }: BadgeProps) {
  let styles = "bg-gray-50 text-gray-700 ring-gray-600/20";

  if (variant === "risk" && value) {
    styles = riskStyles[value as RiskLevel] || styles;
  }
  if (variant === "severity" && value) {
    styles = severityStyles[value as FraudSeverity] || styles;
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
