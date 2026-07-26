export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="card card-pad flex flex-col items-start gap-3 border-danger/40"
    >
      <div>
        <p className="text-sm font-semibold text-danger">
          Something went wrong loading this data
        </p>
        <p className="mt-1 text-sm text-ink-muted">{message}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
