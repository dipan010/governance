import type { RouteObject } from "react-router-dom";
import App from "./App";
import { EmptyState } from "./components/EmptyState";
import { AuditView } from "./screens/AuditView";
import { Dashboard } from "./screens/Dashboard";
import { RouteView } from "./screens/RouteView";
import { ViolationDetail } from "./screens/ViolationDetail";
import { Worklist } from "./screens/Worklist";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "worklist", element: <Worklist /> },
      { path: "violations/:id", element: <ViolationDetail /> },
      { path: "violations/:id/route", element: <RouteView /> },
      { path: "violations/:id/audit", element: <AuditView /> },
      {
        path: "*",
        element: (
          <EmptyState
            title="Page not found"
            description="That route does not exist in this console."
          />
        ),
      },
    ],
  },
];
