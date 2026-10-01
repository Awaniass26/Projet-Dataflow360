/**
 * Indicateur de chargement simple
 */

export function Loading({ message = "Chargement..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      <p className="mt-4 text-sm text-gray-500">{message}</p>
    </div>
  );
}

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      {message}
    </div>
  );
}
