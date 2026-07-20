// Typed API contracts mirroring the backend response models.

export interface ViolationSummary {
  violationId: string;
  policyId: string;
  policyName: string | null;
  resourceId: string;
  severity: string;
  complianceState: string;
  actionStatus: string;
  missingEvidence: string[];
  riskScore: number | null;
  riskBand: string | null;
  blockers: string[];
  actionabilityScore: number | null;
  route: string | null;
  environment: string | null;
  exposure: string | null;
  dataClassification: string | null;
  ownerTeam: string | null;
  ownerConfidence: string | null;
  businessApp: string | null;
  sourceDriftLikely: boolean | null;
}

export interface Decision {
  riskScore: number | null;
  riskBand: string | null;
  scoreFactors: string[];
  blockers: string[];
  recommendedPath: string | null;
  approvalRequired: boolean | null;
  approverRole: string | null;
  rollbackOrNextAction: string | null;
  actionabilityScore: number | null;
  actionabilityFactors: string[];
  scoreRuleVersion: string | null;
  routeRuleVersion: string | null;
}

export interface Evidence {
  schemaVersion: string;
  violationId: string;
  policyEvidence: {
    policyId: string;
    policyName: string;
    assignmentId: string | null;
    initiative: string | null;
    complianceState: string;
    failureReason: string | null;
    evaluatedAt: string;
  };
  resourceFacts: {
    resourceId: string;
    resourceType: string | null;
    environment: string;
    resourceGroup: string | null;
    tags: Record<string, string>;
  };
  riskSignals: {
    severity: string;
    dataClassification: string;
    internetExposure: boolean | null;
    identityImpact: boolean | null;
    regulatoryControl: string | null;
    focusedSignals: string[];
  };
  ownership: {
    ownerTeam: string | null;
    ownerEmail: string | null;
    businessApp: string | null;
    repoUrl: string | null;
    repoPath: string | null;
    codeOwner: string | null;
    ownerConfidence: string;
  };
  history: {
    recurrenceCount: number;
    previousFix: string | null;
    sourceDriftLikely: boolean | null;
    sourceConfidence: string;
  };
  decision: Decision;
  actionState: {
    approver: string | null;
    approvedAt: string | null;
    ticketId: string | null;
    prUrl: string | null;
    remediationTaskId: string | null;
    actionStatus: string;
  };
  verification: {
    beforeState: Record<string, unknown> | null;
    afterState: Record<string, unknown> | null;
    verificationQuery: string | null;
    expectedCompliantValue: string | null;
    verificationResult: string;
    nextAction: string | null;
  };
}

export interface ApprovalRecord {
  approvalId: string;
  status: string;
  approverRole: string | null;
  approver: string | null;
  reason: string | null;
  payload: Record<string, unknown>;
}

export interface ViolationDetail {
  violationId: string;
  evidence: Evidence;
  missingEvidence: string[];
  rawEvidence: Record<string, unknown> | null;
  approvals: ApprovalRecord[];
}

export interface Artifact {
  artifactId: string;
  violationId: string;
  kind: string;
  title: string;
  body: string;
  requiresApproval: boolean;
  approvalState: string;
  isDraft: boolean;
  createdAt: string;
}

export interface AuditEvent {
  eventId: string;
  violationId: string;
  eventType: string;
  correlationId: string;
  actionId: string | null;
  promptRunId: string;
  evidencePacket: string | null;
  payload: Record<string, unknown>;
  createdAt: string;
}

export interface VerifyResponse {
  violationId: string;
  result: string;
  beforeState: Record<string, unknown> | null;
  afterState: Record<string, unknown> | null;
  verificationQuery: string | null;
  expectedCompliantValue: string | null;
  details: string[];
  nextAction: string;
  actionStatus: string;
  ruleVersion: string;
}

export interface DashboardSummary {
  totalFindings: number;
  criticalFindings: number;
  repeatViolations: number;
  autoRemediable: number;
  tickets: number;
  prComments: number;
  exceptions: number;
  blockedUnsafeActions: number;
  verifiedFixes: number;
}

export type SortMode = "raw" | "ranked";
