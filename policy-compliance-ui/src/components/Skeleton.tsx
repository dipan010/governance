export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`relative overflow-hidden rounded bg-surface-sunken ${className}`}
      aria-hidden="true"
    >
      <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-line/50 to-transparent [animation:shimmer_1.6s_infinite]" />
    </div>
  );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2" role="status" aria-label="Loading">
      <Skeleton className="h-8 w-full" />
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-12 w-full" />
      ))}
      <span className="sr-only">Loading data</span>
    </div>
  );
}

export function StatTileSkeleton({ tiles = 9 }: { tiles?: number }) {
  return (
    <div
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9"
      role="status"
      aria-label="Loading metrics"
    >
      {Array.from({ length: tiles }).map((_, index) => (
        <Skeleton key={index} className="h-20" />
      ))}
      <span className="sr-only">Loading metrics</span>
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="card card-pad flex flex-col gap-3" role="status">
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-24 w-full" />
      <span className="sr-only">Loading card</span>
    </div>
  );
}
