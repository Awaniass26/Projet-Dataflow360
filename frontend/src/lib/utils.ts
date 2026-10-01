import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utilitaire pour fusionner des classes Tailwind proprement.
 * Évite les conflits de classes (ex: "p-2 p-4" → "p-4").
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formate un score de crédit pour l'affichage
 * Ex: 720 → "720"
 */
export function formatScore(score: number): string {
  return Math.round(score).toString();
}

/**
 * Retourne la couleur associée à un niveau de risque
 */
export function getRiskColor(risk: "faible" | "moyen" | "élevé"): string {
  switch (risk) {
    case "faible":
      return "text-success bg-green-50";
    case "moyen":
      return "text-warning bg-orange-50";
    case "élevé":
      return "text-danger bg-red-50";
    default:
      return "text-gray-600 bg-gray-50";
  }
}

/**
 * Formate un montant en FCFA (ou autre devise)
 */
export function formatAmount(amount: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "XOF",
    maximumFractionDigits: 0,
  }).format(amount);
}
