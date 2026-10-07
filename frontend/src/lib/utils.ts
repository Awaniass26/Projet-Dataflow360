import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatAmount(amount: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "XOF",
    maximumFractionDigits: 0,
  }).format(amount ?? 0);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("fr-FR").format(value ?? 0);
}

export function formatPercent(value: number, digits = 1): string {
  return `${((value ?? 0) * 100).toFixed(digits)} %`;
}
