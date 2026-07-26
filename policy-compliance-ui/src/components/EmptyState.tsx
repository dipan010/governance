export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="card card-pad flex flex-col items-center gap-2 py-10 text-center">
      <p className="text-sm font-semibold text-ink">{title}</p>
      {description && (
        <p className="max-w-md text-sm text-ink-muted">{description}</p>
      )}
      {action}
    </div>
  );
}
