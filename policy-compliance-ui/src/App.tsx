import { NavLink, Outlet } from "react-router-dom";
import { ThemeToggle } from "./components/ThemeToggle";
import { dataSourceLabel } from "./data/dataClient";
import { dismissToast, useToasts } from "./store/useToast";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/worklist", label: "Worklist", end: false },
];

function ToastRegion() {
  const toasts = useToasts();
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role={toast.tone === "error" ? "alert" : "status"}
          className={`card card-pad flex items-start justify-between gap-3 shadow-lg ${
            toast.tone === "error"
              ? "border-danger/50"
              : toast.tone === "success"
                ? "border-success/50"
                : "border-line"
          }`}
        >
          <p className="text-sm text-ink">{toast.message}</p>
          <button
            type="button"
            aria-label="Dismiss notification"
            className="text-ink-subtle hover:text-ink"
            onClick={() => dismissToast(toast.id)}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-accent focus:px-3 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-line bg-surface-raised/95 backdrop-blur">
        <div className="mx-auto flex max-w-[110rem] flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="grid h-8 w-8 place-items-center rounded bg-accent text-sm font-bold text-white"
            >
              PC
            </span>
            <div>
              <p className="text-sm font-semibold text-ink">
                Policy Compliance &amp; Drift Detection
              </p>
              <p className="text-[11px] text-ink-subtle">
                ABI TECHOPS CLOUD ENGG · ghq-3-squad3-cloudgov-dev-rg
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="chip border-line bg-surface-sunken text-ink-muted">
              {dataSourceLabel}
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-[110rem] flex-1 gap-4 px-4 py-4">
        <nav aria-label="Primary" className="hidden w-44 shrink-0 md:block">
          <ul className="sticky top-20 flex flex-col gap-1">
            {NAV.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-accent-soft text-accent"
                        : "text-ink-muted hover:bg-surface-sunken hover:text-ink"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <main id="main" className="min-w-0 flex-1">
          {/* Mobile nav */}
          <nav aria-label="Primary mobile" className="mb-3 flex gap-2 md:hidden">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm font-medium ${
                    isActive
                      ? "bg-accent text-white"
                      : "border border-line text-ink-muted"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <Outlet />
        </main>
      </div>

      <ToastRegion />
    </div>
  );
}
