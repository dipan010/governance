import type {
  DashboardSummary,
  Evidence,
  ViolationDetail,
  ViolationSummary,
} from "../api/types";

export const summaryFixture: DashboardSummary = {
  totalFindings: 5,
  criticalFindings: 1,
  repeatViolations: 2,
  autoRemediable: 1,
  tickets: 2,
  prComments: 1,
  exceptions: 1,
  blockedUnsafeActions: 1,
  verifiedFixes: 1,
};

export const worklistFixture: ViolationSummary[] = [
  {
    violationId: "POL-002",
    policyId: "nsg-restrict-management-ports",
    policyName: "Management ports should be closed",
    resourceId: "/subscriptions/x/nsg-app-prod-01",
    severity: "Critical",
    complianceState: "NonCompliant",
    actionStatus: "Open",
    missingEvidence: [],
    riskScore: 60,
    riskBand: "High",
    blockers: ["unknown_downtime_risk", "production_runtime_change"],
    actionabilityScore: 5,
    route: "owner_ticket_or_change_request",
    environment: "Production",
    exposure: "internet exposed",
    dataClassification: "Internal",
    ownerTeam: "Web Frontline",
    ownerConfidence: "High",
    businessApp: "WebFront",
    sourceDriftLikely: null,
  },
  {
    violationId: "POL-001",
    policyId: "storage-public-network-disabled",
    policyName: "Storage accounts should restrict public network access",
    resourceId: "/subscriptions/x/stpayprod01",
    severity: "High",
    complianceState: "NonCompliant",
    actionStatus: "Open",
    missingEvidence: [],
    riskScore: 100,
    riskBand: "Critical",
    blockers: ["production_runtime_change"],
    actionabilityScore: 20,
    route: "source_pr_plus_change_ticket",
    environment: "Production",
    exposure: "internet exposed",
    dataClassification: "Restricted",
    ownerTeam: "Payments Platform",
    ownerConfidence: "High",
    businessApp: "Payments",
    sourceDriftLikely: true,
  },
  {
    violationId: "POL-005",
    policyId: "public-ip-network-rule-drift",
    policyName: "Public IPs must have an owner",
    resourceId: "/subscriptions/x/pip-legacy-app-01",
    severity: "Medium",
    complianceState: "NonCompliant",
    actionStatus: "Blocked",
    missingEvidence: ["missing_owner"],
    riskScore: 20,
    riskBand: "Low",
    blockers: ["missing_owner", "unknown_downtime_risk"],
    actionabilityScore: 0,
    route: "blocked_manual_review",
    environment: "Unknown",
    exposure: "internet exposed",
    dataClassification: "Unknown",
    ownerTeam: null,
    ownerConfidence: "Low",
    businessApp: null,
    sourceDriftLikely: null,
  },
];

function evidenceBase(): Evidence {
  return {
    schemaVersion: "1.1.0",
    violationId: "POL-001",
    policyEvidence: {
      policyId: "storage-public-network-disabled",
      policyName: "Storage accounts should restrict public network access",
      assignmentId: "cloud-governance-baseline",
      initiative: "Azure Security Benchmark",
      complianceState: "NonCompliant",
      failureReason: "publicNetworkAccess is Enabled",
      evaluatedAt: "2026-07-18T10:00:00+00:00",
    },
    resourceFacts: {
      resourceId:
        "/subscriptions/1a2b3c4d/resourceGroups/ghq-3-squad3-cloudgov-dev-rg/providers/Microsoft.Storage/storageAccounts/stpayprod01",
      resourceType: "Microsoft.Storage/storageAccounts",
      environment: "Production",
      resourceGroup: "ghq-3-squad3-cloudgov-dev-rg",
      tags: { app: "payments" },
    },
    riskSignals: {
      severity: "High",
      dataClassification: "Restricted",
      internetExposure: true,
      identityImpact: false,
      regulatoryControl: "Network Security",
      focusedSignals: [
        "storage_public_network_access",
        "storage_firewall_default_allow",
        "private_endpoint_gap",
        "source_drift_likely",
      ],
    },
    ownership: {
      ownerTeam: "Payments Platform",
      ownerEmail: "payments-platform@example.com",
      businessApp: "Payments",
      repoUrl: "https://github.com/dipan010/cloudgov-iac",
      repoPath: "terraform/storage/payments/storage_account.tf",
      codeOwner: "@payments-platform",
      ownerConfidence: "High",
    },
    history: {
      recurrenceCount: 2,
      previousFix: "Runtime patch on 2026-07-03",
      sourceDriftLikely: true,
      sourceConfidence: "High",
    },
    decision: {
      riskScore: 100,
      riskBand: "Critical",
      scoreFactors: ["high or critical severity (+20)", "internet exposure (+20)"],
      blockers: ["production_runtime_change"],
      recommendedPath: "source_pr_plus_change_ticket",
      approvalRequired: true,
      approverRole: "Cloud Governance Approver",
      rollbackOrNextAction: "Revert the source PR if the deployment misbehaves",
      actionabilityScore: 20,
      actionabilityFactors: ["owner confidence (+20)", "blocker weight (-30)"],
      scoreRuleVersion: "risk-1.0.0",
      routeRuleVersion: "route-1.0.0",
    },
    actionState: {
      approver: null,
      approvedAt: null,
      ticketId: null,
      prUrl: null,
      remediationTaskId: null,
      actionStatus: "Open",
    },
    verification: {
      beforeState: { publicNetworkAccess: "Enabled" },
      afterState: null,
      verificationQuery:
        "resources | where id =~ '<resourceId>' | project publicNetworkAccess",
      expectedCompliantValue: "publicNetworkAccess == Disabled",
      verificationResult: "NotRun",
      nextAction: null,
    },
  };
}

export const pol001Detail: ViolationDetail = {
  violationId: "POL-001",
  evidence: evidenceBase(),
  missingEvidence: [],
  rawEvidence: { findingRef: "POL-001" },
  approvals: [],
};

export function pol005Detail(): ViolationDetail {
  const evidence = evidenceBase();
  evidence.violationId = "POL-005";
  evidence.policyEvidence.policyName = "Public IPs must have an owner";
  evidence.ownership.ownerTeam = null;
  evidence.ownership.ownerConfidence = "Low";
  evidence.ownership.repoUrl = null;
  evidence.ownership.repoPath = null;
  evidence.history.sourceDriftLikely = null;
  evidence.history.sourceConfidence = "Unknown";
  evidence.decision.recommendedPath = "blocked_manual_review";
  evidence.decision.approvalRequired = false;
  evidence.decision.blockers = [
    "missing_owner",
    "unknown_downtime_risk",
    "unknown_dependency_impact",
  ];
  evidence.actionState.actionStatus = "Blocked";
  return {
    violationId: "POL-005",
    evidence,
    missingEvidence: ["missing_owner", "missing_repo_map"],
    rawEvidence: { findingRef: "POL-005" },
    approvals: [],
  };
}
