// Canonical evidence contract. Mirrors the backend schema 1:1 so swapping
// the mock client for the real API changes no types.

export type RiskBand = "Critical" | "High" | "Medium" | "Low";

export type Severity = "Critical" | "High" | "Medium" | "Low" | "Unknown";

export type EnvironmentType =
  | "Production"
  | "Staging"
  | "Development"
  | "Unknown";

export type DataClassification =
  | "Restricted"
  | "Confidential"
  | "Internal"
  | "Public"
  | "Unknown";

export type ConfidenceLevel = "High" | "Medium" | "Low" | "Unknown";

export type RoutePath =
  | "source_pr_plus_change_ticket"
  | "remediation_dry_run"
  | "owner_ticket_or_change_request"
  | "time_bound_exception"
  | "blocked_manual_review"
  | "escalation"
  | "observe"
  | "invalid_finding";

export type ActionStatus =
  | "Open"
  | "AwaitingApproval"
  | "Approved"
  | "Rejected"
  | "ArtifactCreated"
  | "VerificationPending"
  | "Verified"
  | "Closed"
  | "Blocked";

export type ApprovalState =
  | "NotRequested"
  | "Requested"
  | "Approved"
  | "Rejected"
  | "Deferred";

export type VerificationResult = "NotRun" | "Compliant" | "Failed";

export type ImpactLevel = "None" | "Low" | "Medium" | "High" | "Unknown";

export type ArtifactKind =
  | "ticket"
  | "pr_comment_preview"
  | "remediation_dry_run"
  | "exception_request"
  | "blocked_card"
  | "escalation_note";

export interface PolicyEvidence {
  policyId: string;
  policyName: string;
  assignmentId: string | null;
  initiative: string | null;
  complianceState: string;
  failureReason: string | null;
  evaluatedAt: string;
}

export interface ResourceFacts {
  resourceId: string;
  resourceType: string;
  subscriptionId: string;
  resourceGroup: string;
  location: string;
  tags: Record<string, string>;
  environment: EnvironmentType;
  productionCriticality: string;
}

export interface RiskSignals {
  severity: Severity;
  dataClassification: DataClassification;
  internetExposure: boolean;
  identityImpact: boolean;
  dependencyCount: number | null;
  regulatoryControl: string | null;
  focusedSignals: string[];
}

export interface Ownership {
  ownerTeam: string | null;
  ownerEmail: string | null;
  supportGroup: string | null;
  businessApp: string | null;
  repoUrl: string | null;
  repoPath: string | null;
  codeOwner: string | null;
  ownerConfidence: ConfidenceLevel;
}

export interface RemediationEligibility {
  policyEffect: string;
  remediationSupported: boolean;
  requiredPermission: string | null;
  permissionAvailable: boolean;
  restartRisk: ImpactLevel;
  downtimeRisk: ImpactLevel;
  costImpact: ImpactLevel;
}

export interface History {
  firstSeen: string;
  lastSeen: string;
  previousFix: string | null;
  recurrenceCount: number;
  sourceDriftLikely: boolean;
  sourceConfidence: ConfidenceLevel;
}

/** A single scoring driver. The server owns the points; the UI only renders. */
export interface ScoreFactor {
  label: string;
  points: number;
}

export interface Decision {
  riskScore: number;
  riskBand: RiskBand;
  scoreFactors: ScoreFactor[];
  blockers: string[];
  recommendedPath: RoutePath;
  routeReason: string;
  sideEffects: string[];
  approvalRequired: boolean;
  approverRole: string | null;
  rollbackOrNextAction: string;
  actionabilityScore: number;
  scoreRuleVersion: string;
  routeRuleVersion: string;
}

export interface ActionState {
  approver: string | null;
  approvedAt: string | null;
  ticketId: string | null;
  prUrl: string | null;
  remediationTaskId: string | null;
  actionStatus: ActionStatus;
  approvalState: ApprovalState;
  rejectionReason: string | null;
}

export interface Verification {
  beforeState: Record<string, string> | null;
  afterState: Record<string, string> | null;
  verificationQuery: string;
  expectedCompliantValue: string;
  verificationResult: VerificationResult;
  nextAction: string;
}

export interface SourceMapEntry {
  property: string;
  currentValue: string;
  expectedValue: string;
  runtimeProperty: string;
}

export interface Violation {
  schemaVersion: string;
  violationId: string;
  policyEvidence: PolicyEvidence;
  resourceFacts: ResourceFacts;
  riskSignals: RiskSignals;
  ownership: Ownership;
  remediationEligibility: RemediationEligibility;
  history: History;
  decision: Decision;
  actionState: ActionState;
  verification: Verification;
  sourceMap: SourceMapEntry[];
  missingEvidence: string[];
}

export interface IngestResult {
  ingestId: string;
  ingested: number;
  errors: number;
}

export interface RouteRecommendation {
  violationId: string;
  route: RoutePath;
  reason: string;
  blockers: string[];
  approvalRequired: boolean;
  approverRole: string | null;
  sideEffects: string[];
  rollbackOrNextAction: string;
  routeRuleVersion: string;
}

export interface ApprovalPayload {
  approvalId: string;
  violationId: string;
  approvalState: ApprovalState;
  approverRole: string | null;
  route: RoutePath;
  riskScore: number;
  riskBand: RiskBand;
  blastRadius: string;
  affectedResources: string[];
  restartRisk: ImpactLevel;
  downtimeRisk: ImpactLevel;
  expectedAfterState: Record<string, string>;
  rollbackOrNextAction: string;
  verificationQuery: string;
  requestedAt: string;
}

export interface ApprovalDecision {
  decision: "approve" | "reject";
  approver: string;
  reason?: string;
}

export interface Artifact {
  artifactId: string;
  violationId: string;
  kind: ArtifactKind;
  title: string;
  /** Rendered body: markdown-ish text, or a unified diff for PR previews. */
  body: string;
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
  detail: string;
  createdAt: string;
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
  highRiskActionable: Array<{
    violationId: string;
    policyName: string;
    riskScore: number;
    riskBand: RiskBand;
    route: RoutePath;
  }>;
  highRiskBlocked: Array<{
    violationId: string;
    policyName: string;
    riskScore: number;
    riskBand: RiskBand;
    blockers: string[];
  }>;
}

export interface WorklistFilters {
  policy?: string;
  severity?: string;
  riskBand?: string;
  exposure?: string;
  dataClassification?: string;
  owner?: string;
  app?: string;
  sourceDrift?: string;
  route?: string;
  confidence?: string;
  status?: string;
  blocker?: string;
}

export type RankMode = "raw" | "ranked";
