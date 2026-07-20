import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ComplianceSummary } from "../components/ComplianceSummary";
import { FindingCard } from "../components/FindingCard";
import { Worklist } from "../components/Worklist";
import {
  pol001Detail,
  pol005Detail,
  summaryFixture,
  worklistFixture,
} from "./fixtures";

const noop = () => undefined;

function renderCard(detail = pol001Detail) {
  return render(
    <FindingCard
      detail={detail}
      artifacts={[]}
      audit={[]}
      busy={false}
      onRequestApproval={noop}
      onDecideApproval={noop}
      onGenerateArtifacts={noop}
      onVerify={noop}
      onClose={noop}
    />,
  );
}

describe("ComplianceSummary", () => {
  it("renders all summary metrics", () => {
    render(<ComplianceSummary summary={summaryFixture} />);
    expect(screen.getByText("Total findings")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("Blocked unsafe actions")).toBeInTheDocument();
    expect(screen.getByText("Verified fixes")).toBeInTheDocument();
    const summary = screen.getByLabelText("Compliance summary");
    expect(within(summary).getByText("5")).toBeInTheDocument();
  });
});

describe("Worklist", () => {
  it("toggles between raw severity and agent ranking", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    render(
      <Worklist
        violations={worklistFixture}
        sort="ranked"
        onSortChange={onSortChange}
        selectedId={null}
        onSelect={noop}
      />,
    );
    expect(screen.getByRole("button", { name: "Agent-ranked" })).toHaveClass(
      "active",
    );
    await user.click(screen.getByRole("button", { name: "Raw severity" }));
    expect(onSortChange).toHaveBeenCalledWith("raw");
  });

  it("shows blockers as first-class information and filters by blocker", async () => {
    const user = userEvent.setup();
    render(
      <Worklist
        violations={worklistFixture}
        sort="ranked"
        onSortChange={noop}
        selectedId={null}
        onSelect={noop}
      />,
    );
    expect(screen.getAllByText(/missing_owner/).length).toBeGreaterThan(0);
    await user.selectOptions(
      screen.getByLabelText("Filter by blocker"),
      "missing_owner",
    );
    const rows = screen.getAllByRole("row").slice(1); // skip header
    expect(rows).toHaveLength(1);
    expect(within(rows[0]).getByText("POL-005")).toBeInTheDocument();
  });

  it("offers all required filters", () => {
    render(
      <Worklist
        violations={worklistFixture}
        sort="ranked"
        onSortChange={noop}
        selectedId={null}
        onSelect={noop}
      />,
    );
    for (const label of [
      "policy",
      "severity",
      "exposure",
      "data classification",
      "owner",
      "app",
      "source drift",
      "route",
      "confidence",
      "status",
      "blocker",
    ]) {
      expect(screen.getByLabelText(`Filter by ${label}`)).toBeInTheDocument();
    }
  });
});

describe("FindingCard for POL-001 (critical)", () => {
  it("shows the PR/comment plus ticket route with score factors", () => {
    renderCard();
    expect(
      screen.getByText("Source PR/comment plus change ticket"),
    ).toBeInTheDocument();
    expect(screen.getByText(/high or critical severity/)).toBeInTheDocument();
    expect(screen.getByText(/Risk score/)).toBeInTheDocument();
    expect(screen.getByLabelText("Verification")).toHaveTextContent(
      "publicNetworkAccess",
    );
  });

  it("disables the artifact action without approval", () => {
    renderCard();
    const button = screen.getByRole("button", { name: "Generate route artifact" });
    expect(button).toBeDisabled();
    expect(
      screen.getByText("Disabled until an approval is granted."),
    ).toBeInTheDocument();
  });

  it("enables the artifact action once approved", () => {
    const detail = {
      ...pol001Detail,
      approvals: [
        {
          approvalId: "a1",
          status: "Approved",
          approverRole: "Cloud Governance Approver",
          approver: "cloudgov-approver",
          reason: null,
          payload: {},
        },
      ],
    };
    renderCard(detail);
    expect(
      screen.getByRole("button", { name: "Generate route artifact" }),
    ).toBeEnabled();
  });

  it("disables closure until verification proves compliance", () => {
    renderCard();
    expect(screen.getByRole("button", { name: "Close violation" })).toBeDisabled();
  });
});

describe("FindingCard for POL-005 (blocked)", () => {
  it("shows the blocked route, owner gap, and blockers", () => {
    renderCard(pol005Detail());
    expect(screen.getByText("Blocked: manual review")).toBeInTheDocument();
    expect(screen.getByText(/OWNER GAP/)).toBeInTheDocument();
    const blockers = screen.getByLabelText("Blockers");
    expect(within(blockers).getByText("missing_owner")).toBeInTheDocument();
    expect(
      within(blockers).getByText("unknown_dependency_impact"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Missing evidence")).toHaveTextContent(
      "missing_owner",
    );
  });
});
