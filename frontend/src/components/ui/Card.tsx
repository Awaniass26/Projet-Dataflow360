/**
 * Composant Card réutilisable
 */

import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white p-6 shadow-sm",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, className }: CardProps) {
  return (
    <h3 className={cn("text-sm font-medium text-gray-500", className)}>
      {children}
    </h3>
  );
}

export function CardValue({ children, className }: CardProps) {
  return (
    <p className={cn("mt-2 text-3xl font-bold text-gray-900", className)}>
      {children}
    </p>
  );
}
