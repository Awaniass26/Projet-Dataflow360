export function Loading({ message = "Chargement..." }: { message?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3">
      <div className="h-9 w-9 animate-spin rounded-full border-[3px] border-brand-blue/20 border-t-brand-blue" />
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
}

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="max-w-md rounded-2xl border border-red-100 bg-red-50 px-6 py-5 text-center">
        <p className="text-sm font-medium text-red-700">{message}</p>
      </div>
    </div>
  );
}
