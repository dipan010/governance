import type { Artifact, AuditEvent, Violation } from "../types";

const SUB = "/subscriptions/1a2b3c4d-0000-4000-8000-000000000001";
const RG = `${SUB}/resourceGroups/ghq-3-squad3-cloudgov-dev-rg`;

/**
 * Five canonical findings. Scores and routes are produced by the backend's
 * deterministic engine; these values are recorded server outputs, never
 * recomputed in the browser.
 *
 * Raw severity order:  POL-002, POL-005, POL-001, POL-004, POL-003
 * Agent-ranked order:  POL-001, POL-002, POL-004, POL-003, POL-005
 */
export const seedViolations: Violation[] = [
  {
    schemaVersion: "1.0.0",
    violationId: "POL-001",
    policyEvidence: {
      policyId: "storage-public-network-disabled",
      policyName: "Storage accounts should restrict public network access",
      assignmentId: "cloud-governance-baseline",
      initiative: "Azure Security Benchmark",
      complianceState: "NonCompliant",
      failureReason: "publicNetworkAccess is Enabled",
      evaluatedAt: "2026-07-09T10:00:00Z",
    },
    resourceFacts: {
      resourceId: `${RG}/providers/Microsoft.Storage/storageAccounts/stpayprod01`,
      resourceType: "Microsoft.Storage/storageAccounts",
      subscriptionId: "ABI TECHOPS CLOUD ENGG",
      resourceGroup: "ghq-3-squad3-cloudgov-dev-rg",
      location: "eastus",
      tags: { app: "payments", environment: "prod" },
      environment: "Production",
      productionCriticality: "High",
    },
    riskSignals: {
      severity: "High",
      dataClassification: "Restricted",
      internetExposure: true,
      identityImpact: false,
      dependencyCount: 6,
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
      supportGroup: "CloudOps-Payments",
      businessApp: "Payments",
      repoUrl: "https://github.com/org/cloudgov-iac",
      repoPath: "terraform/storage/payments/storage_account.tf",
      codeOwner: "@payments-platform",
      ownerConfidence: "High",
    },
    remediationEligibility: {
      policyEffect: "Audit",
      remediationSupported: false,
      requiredPermission: "Microsoft.Storage/storageAccounts/write",
      permissionAvailable: false,
      restartRisk: "None",
      downtimeRisk: "Low",
      costImpact: "None",
    },
    history: {
      firstSeen: "2026-07-01T09:00:00Z",
      lastSeen: "2026-07-09T10:00:00Z",
      previousFix: "Runtime patch on 2026-07-03",
      recurrenceCount: 2,
      sourceDriftLikely: true,
      sourceConfidence: "High",
    },
    decision: {
      riskScore: 94,
      riskBand: "Critical",
      scoreFactors: [
        { label: "High severity", points: 20 },
        { label: "Production resource", points: 15 },
        { label: "Restricted data", points: 20 },
        { label: "Internet exposed", points: 20 },
        { label: "Recurring violation", points: 15 },
        { label: "Source drift likely", points: 10 },
        { label: "Strong owner confidence", points: 5 },
      ],
      blockers: ["production_runtime_change"],
      recommendedPath: "source_pr_plus_change_ticket",
      routeReason:
        "Source drift detected with a mapped repo path; a runtime-only patch would be temporary, so the source of truth is fixed first.",
      sideEffects: [
        "restart risk: None",
        "downtime risk: Low",
        "cost impact: None",
        "production resource: runtime change affects live traffic",
      ],
      approvalRequired: true,
      approverRole: "Cloud Governance Approver",
      rollbackOrNextAction:
        "Revert the source PR or restore the previous network rule if an approved exception exists",
      actionabilityScore: 62,
      scoreRuleVersion: "risk-1.0.0",
      routeRuleVersion: "route-1.0.0",
    },
    actionState: {
      approver: "cloudgov-approver",
      approvedAt: "2026-07-09T12:10:00Z",
      ticketId: "CHG-48213",
      prUrl: null,
      remediationTaskId: null,
      actionStatus: "Verified",
      approvalState: "Approved",
      rejectionReason: null,
    },
    verification: {
      beforeState: {
        publicNetworkAccess: "Enabled",
        "networkAcls.defaultAction": "Allow",
      },
      afterState: {
        publicNetworkAccess: "Disabled",
        "networkAcls.defaultAction": "Deny",
      },
      verificationQuery:
        "resources | where id =~ '<resourceId>' | project publicNetworkAccess=properties.publicNetworkAccess, defaultAction=properties.networkAcls.defaultAction",
      expectedCompliantValue:
        "publicNetworkAccess == Disabled and networkAcls.defaultAction == Deny",
      verificationResult: "Compliant",
      nextAction:
        "Close the violation; the evidence packet holds before/after proof",
    },
    sourceMap: [
      {
        property: "public_network_access_enabled",
        currentValue: "true",
        expectedValue: "false",
        runtimeProperty: "publicNetworkAccess",
      },
      {
        property: "network_rules.default_action",
        currentValue: "Allow",
        expectedValue: "Deny",
        runtimeProperty: "networkAcls.defaultAction",
      },
    ],
    missingEvidence: [],
  },
  {
    schemaVersion: "1.0.0",
    violationId: "POL-002",
    policyEvidence: {
      policyId: "nsg-restrict-management-ports",
      policyName: "Management ports should be closed on network security groups",
      assignmentId: "cloud-governance-baseline",
      initiative: "Azure Security Benchmark",
      complianceState: "NonCompliant",
      failureReason:
        "Inbound rule allow-ssh-inbound permits 0.0.0.0/0 to destination port 22",
      evaluatedAt: "2026-07-09T10:05:00Z",
    },
    resourceFacts: {
      resourceId: `${RG}/providers/Microsoft.Network/networkSecurityGroups/nsg-app-prod-01`,
      resourceType: "Microsoft.Network/networkSecurityGroups",
      subscriptionId: "ABI TECHOPS CLOUD ENGG",
      resourceGroup: "ghq-3-squad3-cloudgov-dev-rg",
      location: "eastus",
      tags: { app: "webfront", environment: "prod" },
      environment: "Production",
      productionCriticality: "High",
    },
    riskSignals: {
      severity: "Critical",
      dataClassification: "Internal",
      internetExposure: true,
      identityImpact: false,
      dependencyCount: null,
      regulatoryControl: "Network Security",
      focusedSignals: [
        "broad_source_cidr",
        "sensitive_port_exposed",
        "priority_drift",
      ],
    },
    ownership: {
      ownerTeam: null,
      ownerEmail: null,
      supportGroup: null,
      businessApp: "WebFront",
      repoUrl: null,
      repoPath: null,
      codeOwner: null,
      ownerConfidence: "Low",
    },
    remediationEligibility: {
      policyEffect: "Audit",
      remediationSupported: false,
      requiredPermission: "Microsoft.Network/networkSecurityGroups/write",
      permissionAvailable: false,
      restartRisk: "Unknown",
      downtimeRisk: "Unknown",
      costImpact: "None",
    },
    history: {
      firstSeen: "2026-07-08T08:00:00Z",
      lastSeen: "2026-07-09T10:05:00Z",
      previousFix: null,
      recurrenceCount: 0,
      sourceDriftLikely: false,
      sourceConfidence: "Unknown",
    },
    decision: {
      riskScore: 75,
      riskBand: "High",
      scoreFactors: [
        { label: "Critical severity", points: 20 },
        { label: "Production resource", points: 15 },
        { label: "Internet exposed", points: 20 },
        { label: "Management port exposed", points: 20 },
      ],
      blockers: [
        "missing_owner",
        "unknown_downtime_risk",
        "unknown_dependency_impact",
        "production_runtime_change",
      ],
      recommendedPath: "blocked_manual_review",
      routeReason:
        "Owner is missing and dependency impact is unknown; auto-action is blocked until owner discovery completes.",
      sideEffects: [
        "restart risk: Unknown",
        "downtime risk: Unknown",
        "cost impact: None",
        "production resource: runtime change affects live traffic",
      ],
      approvalRequired: false,
      approverRole: null,
      rollbackOrNextAction:
        "Run owner discovery (tags, CMDB, deployment caller), then re-route",
      actionabilityScore: 5,
      scoreRuleVersion: "risk-1.0.0",
      routeRuleVersion: "route-1.0.0",
    },
    actionState: {
      approver: null,
      approvedAt: null,
      ticketId: null,
      prUrl: null,
      remediationTaskId: null,
      actionStatus: "Blocked",
      approvalState: "NotRequested",
      rejectionReason: null,
    },
    verification: {
      beforeState: {
        "allow-ssh-inbound.sourceAddressPrefix": "0.0.0.0/0",
        "allow-ssh-inbound.destinationPortRange": "22",
      },
      afterState: null,
      verificationQuery:
        "resources | where id =~ '<resourceId>' | mv-expand rule=properties.securityRules | where rule.properties.access == 'Allow' and rule.properties.sourceAddressPrefix in ('*','0.0.0.0/0','Internet')",
      expectedCompliantValue:
        "no inbound allow from 0.0.0.0/0 to ports 22 or 3389",
      verificationResult: "NotRun",
      nextAction:
        "Identify the owner, assess dependency impact, then request a change window",
    },
    sourceMap: [],
    missingEvidence: ["missing_owner", "missing_repo_map"],
  },
  {
    schemaVersion: "1.0.0",
    violationId: "POL-003",
    policyEvidence: {
      policyId: "keyvault-purge-protection-enabled",
      policyName: "Key vaults should have purge protection enabled",
      assignmentId: "cloud-governance-baseline",
      initiative: "Azure Security Benchmark",
      complianceState: "NonCompliant",
      failureReason: "enablePurgeProtection is not set",
      evaluatedAt: "2026-07-09T10:10:00Z",
    },
    resourceFacts: {
      resourceId: `${RG}/providers/Microsoft.KeyVault/vaults/kv-govdev-01`,
      resourceType: "Microsoft.KeyVault/vaults",
      subscriptionId: "ABI TECHOPS CLOUD ENGG",
      resourceGroup: "ghq-3-squad3-cloudgov-dev-rg",
      location: "eastus",
      tags: { app: "cloudgov", environment: "dev" },
      environment: "Development",
      productionCriticality: "Low",
    },
    riskSignals: {
      severity: "Low",
      dataClassification: "Confidential",
      internetExposure: false,
      identityImpact: true,
      dependencyCount: 1,
      regulatoryControl: "Data Protection",
      focusedSignals: ["purge_protection_disabled"],
    },
    ownership: {
      ownerTeam: "Cloud Governance",
      ownerEmail: "cloud-governance@example.com",
      supportGroup: "CloudOps-Platform",
      businessApp: "CloudGov",
      repoUrl: "https://github.com/org/cloudgov-iac",
      repoPath: "terraform/keyvault/governance/key_vault.tf",
      codeOwner: "@cloud-governance",
      ownerConfidence: "High",
    },
    remediationEligibility: {
      policyEffect: "Audit",
      remediationSupported: true,
      requiredPermission: "Microsoft.KeyVault/vaults/write",
      permissionAvailable: true,
      restartRisk: "None",
      downtimeRisk: "None",
      costImpact: "None",
    },
    history: {
      firstSeen: "2026-07-05T08:00:00Z",
      lastSeen: "2026-07-09T10:10:00Z",
      previousFix: null,
      recurrenceCount: 0,
      sourceDriftLikely: false,
      sourceConfidence: "High",
    },
    decision: {
      riskScore: 40,
      riskBand: "Medium",
      scoreFactors: [
        { label: "Confidential data", points: 20 },
        { label: "Identity and secrets impact", points: 15 },
        { label: "Strong owner confidence", points: 5 },
      ],
      blockers: [],
      recommendedPath: "remediation_dry_run",
      routeReason:
        "Remediation is supported with permission available on a non-production resource with low side-effect risk; a dry-run may run after approval.",
      sideEffects: [
        "restart risk: None",
        "downtime risk: None",
        "cost impact: None",
      ],
      approvalRequired: true,
      approverRole: "Change Approver",
      rollbackOrNextAction:
        "Review the dry-run plan output; apply only with a separate approved change",
      actionabilityScore: 88,
      scoreRuleVersion: "risk-1.0.0",
      routeRuleVersion: "route-1.0.0",
    },
    // Starts clean so the full request -> approve -> generate journey is
    // demonstrable end to end on this finding.
    actionState: {
      approver: null,
      approvedAt: null,
      ticketId: null,
      prUrl: null,
      remediationTaskId: null,
      actionStatus: "Open",
      approvalState: "NotRequested",
      rejectionReason: null,
    },
    verification: {
      beforeState: { enablePurgeProtection: "false" },
      afterState: null,
      verificationQuery:
        "resources | where id =~ '<resourceId>' | project purgeProtection=properties.enablePurgeProtection",
      expectedCompliantValue: "enablePurgeProtection == true",
      verificationResult: "NotRun",
      nextAction: "Approve the dry-run, review the plan, then schedule the change",
    },
    sourceMap: [
      {
        property: "purge_protection_enabled",
        currentValue: "true",
        expectedValue: "true",
        runtimeProperty: "enablePurgeProtection",
      },
    ],
    missingEvidence: [],
  },
  {
    schemaVersion: "1.0.0",
    violationId: "POL-004",
    policyEvidence: {
      policyId: "postgresql-firewall-restrict-cidr",
      policyName: "PostgreSQL servers should not allow broad public IP ranges",
      assignmentId: "cloud-governance-baseline",
      initiative: "Azure Security Benchmark",
      complianceState: "NonCompliant",
      failureReason:
        "Firewall rule allow-all-temp permits 0.0.0.0-255.255.255.255",
      evaluatedAt: "2026-07-09T10:15:00Z",
    },
    resourceFacts: {
      resourceId: `${RG}/providers/Microsoft.DBforPostgreSQL/flexibleServers/psql-analytics-dev-01`,
      resourceType: "Microsoft.DBforPostgreSQL/flexibleServers",
      subscriptionId: "ABI TECHOPS CLOUD ENGG",
      resourceGroup: "ghq-3-squad3-cloudgov-dev-rg",
      location: "eastus",
      tags: { app: "analytics", environment: "dev" },
      environment: "Development",
      productionCriticality: "Medium",
    },
    riskSignals: {
      severity: "Medium",
      dataClassification: "Confidential",
      internetExposure: true,
      identityImpact: false,
      dependencyCount: 2,
      regulatoryControl: "Network Security",
      focusedSignals: ["database_broad_cidr", "public_endpoint_enabled"],
    },
    ownership: {
      ownerTeam: "Analytics Engineering",
      ownerEmail: "analytics-eng@example.com",
      supportGroup: "CloudOps-Data",
      businessApp: "Analytics",
      repoUrl: null,
      repoPath: null,
      codeOwner: null,
      ownerConfidence: "High",
    },
    remediationEligibility: {
      policyEffect: "Audit",
      remediationSupported: false,
      requiredPermission:
        "Microsoft.DBforPostgreSQL/flexibleServers/firewallRules/write",
      permissionAvailable: false,
      restartRisk: "Low",
      downtimeRisk: "Unknown",
      costImpact: "None",
    },
    history: {
      firstSeen: "2026-06-28T14:00:00Z",
      lastSeen: "2026-07-09T10:15:00Z",
      previousFix: "Rule narrowed on 2026-07-02, widened again during migration",
      recurrenceCount: 1,
      sourceDriftLikely: false,
      sourceConfidence: "Unknown",
    },
    decision: {
      riskScore: 70,
      riskBand: "High",
      scoreFactors: [
        { label: "Confidential data", points: 20 },
        { label: "Internet exposed", points: 20 },
        { label: "Recurring violation", points: 15 },
        { label: "Shared platform resource", points: 10 },
        { label: "Strong owner confidence", points: 5 },
      ],
      blockers: ["unknown_downtime_risk"],
      recommendedPath: "time_bound_exception",
      routeReason:
        "A valid exception request supplies owner, justification, compensating control, and an expiry date for the migration window.",
      sideEffects: [
        "restart risk: Low",
        "downtime risk: Unknown",
        "cost impact: None",
      ],
      approvalRequired: true,
      approverRole: "Security / Compliance Lead",
      rollbackOrNextAction:
        "Review the exception before its expiry date; remove the compensating control only after compliance is restored",
      actionabilityScore: 55,
      scoreRuleVersion: "risk-1.0.0",
      routeRuleVersion: "route-1.0.0",
    },
    actionState: {
      approver: null,
      approvedAt: null,
      ticketId: null,
      prUrl: null,
      remediationTaskId: null,
      actionStatus: "AwaitingApproval",
      approvalState: "Requested",
      rejectionReason: null,
    },
    verification: {
      beforeState: { "allow-all-temp": "0.0.0.0-255.255.255.255" },
      afterState: null,
      verificationQuery:
        "resources | where id =~ '<resourceId>' | mv-expand rule=properties.firewallRules | where rule.startIpAddress == '0.0.0.0'",
      expectedCompliantValue:
        "no firewall rule spanning 0.0.0.0-255.255.255.255",
      verificationResult: "NotRun",
      nextAction:
        "Approve the time-bound exception, then re-verify after the expiry date",
    },
    sourceMap: [],
    missingEvidence: ["missing_repo_map"],
  },
  {
    schemaVersion: "1.0.0",
    violationId: "POL-005",
    policyEvidence: {
      policyId: "public-ip-network-rule-drift",
      policyName: "Public IP addresses must have an owner and approved network rules",
      assignmentId: "cloud-governance-baseline",
      initiative: "Azure Security Benchmark",
      complianceState: "NonCompliant",
      failureReason:
        "Public IP has network rule drift and no owner tag is present",
      evaluatedAt: "2026-07-09T10:20:00Z",
    },
    resourceFacts: {
      resourceId: `${RG}/providers/Microsoft.Network/publicIPAddresses/pip-legacy-app-01`,
      resourceType: "Microsoft.Network/publicIPAddresses",
      subscriptionId: "ABI TECHOPS CLOUD ENGG",
      resourceGroup: "ghq-3-squad3-cloudgov-dev-rg",
      location: "eastus",
      tags: {},
      environment: "Unknown",
      productionCriticality: "Unknown",
    },
    riskSignals: {
      severity: "Medium",
      dataClassification: "Unknown",
      internetExposure: true,
      identityImpact: false,
      dependencyCount: null,
      regulatoryControl: "Asset Management",
      focusedSignals: ["network_rule_drift", "orphaned_public_ip"],
    },
    ownership: {
      ownerTeam: null,
      ownerEmail: null,
      supportGroup: null,
      businessApp: null,
      repoUrl: null,
      repoPath: null,
      codeOwner: null,
      ownerConfidence: "Low",
    },
    remediationEligibility: {
      policyEffect: "Audit",
      remediationSupported: false,
      requiredPermission: "Microsoft.Network/publicIPAddresses/write",
      permissionAvailable: false,
      restartRisk: "Unknown",
      downtimeRisk: "Unknown",
      costImpact: "None",
    },
    history: {
      firstSeen: "2026-05-02T11:00:00Z",
      lastSeen: "2026-07-09T10:20:00Z",
      previousFix: null,
      recurrenceCount: 0,
      sourceDriftLikely: false,
      sourceConfidence: "Unknown",
    },
    decision: {
      riskScore: 20,
      riskBand: "Low",
      scoreFactors: [{ label: "Internet exposed", points: 20 }],
      blockers: [
        "missing_owner",
        "unknown_downtime_risk",
        "unknown_dependency_impact",
        "missing_permission_check",
      ],
      recommendedPath: "blocked_manual_review",
      routeReason:
        "Owner is missing; auto-action is blocked until owner discovery or manual review completes.",
      sideEffects: [
        "restart risk: Unknown",
        "downtime risk: Unknown",
        "cost impact: None",
      ],
      approvalRequired: false,
      approverRole: null,
      rollbackOrNextAction:
        "Run owner discovery or manual review, then re-route",
      actionabilityScore: 0,
      scoreRuleVersion: "risk-1.0.0",
      routeRuleVersion: "route-1.0.0",
    },
    actionState: {
      approver: null,
      approvedAt: null,
      ticketId: null,
      prUrl: null,
      remediationTaskId: null,
      actionStatus: "Blocked",
      approvalState: "NotRequested",
      rejectionReason: null,
    },
    verification: {
      beforeState: { ownerTag: "absent", networkRuleDrift: "true" },
      afterState: null,
      verificationQuery:
        "resources | where id =~ '<resourceId>' | project tags, ipConfiguration=properties.ipConfiguration",
      expectedCompliantValue:
        "owner tag present and network rules match approved baseline",
      verificationResult: "NotRun",
      nextAction: "Owner discovery required before any action can be routed",
    },
    sourceMap: [],
    missingEvidence: ["missing_owner", "missing_repo_map"],
  },
];

export const seedArtifacts: Record<string, Artifact> = {
  "POL-001": {
    artifactId: "art-pol001-pr",
    violationId: "POL-001",
    kind: "pr_comment_preview",
    title:
      "fix(payments-storage): POL-001 — Storage accounts should restrict public network access",
    body: `--- a/terraform/storage/payments/storage_account.tf
+++ b/terraform/storage/payments/storage_account.tf
@@ -12,10 +12,10 @@ resource "azurerm_storage_account" "payments" {
   account_tier             = "Standard"
   account_replication_type = "GRS"

-  public_network_access_enabled = true
+  public_network_access_enabled = false

   network_rules {
-    default_action = "Allow"
+    default_action = "Deny"
     bypass         = ["AzureServices"]
   }
 }`,
    isDraft: true,
    createdAt: "2026-07-09T11:00:00Z",
  },
  "POL-002": {
    artifactId: "art-pol002-blocked",
    violationId: "POL-002",
    kind: "blocked_card",
    title: "Blocked: unsafe action — Management ports should be closed",
    body: `Why this is blocked
- missing_owner: RULES.md 2.7 — missing owner blocks auto-action
- unknown_dependency_impact: RULES.md 2.7 — unknown dependency impact blocks auto-remediation
- unknown_downtime_risk: RULES.md 2.7 — unknown downtime risk blocks auto-remediation
- production_runtime_change: RULES.md 2.3 — production stops at ticket, PR/comment, or dry-run

Safe alternative
- Run owner discovery (tags, CMDB, deployment caller), then re-route
- Map dependencies via Resource Graph before any change
- Owner assesses downtime impact in a change review`,
    isDraft: true,
    createdAt: "2026-07-09T11:05:00Z",
  },
  "POL-003": {
    artifactId: "art-pol003-dryrun",
    violationId: "POL-003",
    kind: "remediation_dry_run",
    title: "Remediation dry-run plan — Key vaults should have purge protection enabled",
    body: `Dry-run plan (what-if only — makes NO live change)

1. Resolve target resource
   kv-govdev-01 (Microsoft.KeyVault/vaults, Development)
2. Evaluate change in what-if mode only
   set properties.enablePurgeProtection = true
3. Required permission
   Microsoft.KeyVault/vaults/write (available: yes)
4. Record what-if output to the evidence packet; make NO live change.
5. Applying the change for real requires a separate approved change.

Expected after-state
   enablePurgeProtection == true`,
    isDraft: true,
    createdAt: "2026-07-09T11:10:00Z",
  },
  "POL-004": {
    artifactId: "art-pol004-exception",
    violationId: "POL-004",
    kind: "exception_request",
    title: "Time-bound exception request — PostgreSQL broad CIDR",
    body: `Exception terms

Exception owner:        Analytics Engineering
Justification:          One-off data migration window requires broad ingress
                        from the partner network whose egress IPs are not fixed.
Compensating control:   Firewall logging enabled, weekly review, alert on any
                        connection outside the partner ASN.
Expiry date:            2026-08-15
Review date:            2026-08-01

Approval and side effects
Approval required:      yes (Security / Compliance Lead)
Restart risk:           Low
Downtime risk:          Unknown

Verification
Query:    resources | where id =~ '<resourceId>' | mv-expand rule=properties.firewallRules
Expected: no firewall rule spanning 0.0.0.0-255.255.255.255`,
    isDraft: true,
    createdAt: "2026-07-09T11:15:00Z",
  },
  "POL-005": {
    artifactId: "art-pol005-blocked",
    violationId: "POL-005",
    kind: "blocked_card",
    title: "Blocked: unsafe action — Public IP must have an owner",
    body: `Why this is blocked
- missing_owner: RULES.md 2.7 — missing owner blocks auto-action
- unknown_downtime_risk: RULES.md 2.7 — unknown downtime risk blocks auto-remediation
- unknown_dependency_impact: RULES.md 2.7 — unknown dependency impact blocks auto-remediation
- missing_permission_check: RULES.md 2.7 — missing permission check blocks runtime action

Safe alternative
- Run owner discovery (tags, CMDB, deployment caller), then re-route
- Verify the managed identity's effective permission first`,
    isDraft: true,
    createdAt: "2026-07-09T11:20:00Z",
  },
};

/** The POL-001 ticket that accompanies its source PR. */
export const seedSecondaryArtifacts: Record<string, Artifact> = {
  "POL-001": {
    artifactId: "art-pol001-ticket",
    violationId: "POL-001",
    kind: "ticket",
    title: "CHG-48213 — Storage accounts should restrict public network access",
    body: `Assignment group:  CloudOps-Payments
Owner:             Payments Platform (payments-platform@example.com)
Business app:      Payments
Change type:       Standard change, source-of-truth repair

Resource
  stpayprod01 (Microsoft.Storage/storageAccounts, Production, Restricted data)

Why now
  Risk 94 (Critical) — high severity, production, restricted data, internet
  exposed, recurring, source drift likely.

What to change
  Merge the source PR against terraform/storage/payments/storage_account.tf,
  then deploy through cloudgov-iac-deploy.

Verification
  publicNetworkAccess == Disabled and networkAcls.defaultAction == Deny`,
    isDraft: true,
    createdAt: "2026-07-09T11:02:00Z",
  },
};

export const seedAudit: Record<string, AuditEvent[]> = {
  "POL-001": [
    {
      eventId: "ev-001",
      violationId: "POL-001",
      eventType: "finding.ingested",
      correlationId: "corr-a1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Ingested from azure_policy_insights export",
      createdAt: "2026-07-09T10:00:05Z",
    },
    {
      eventId: "ev-002",
      violationId: "POL-001",
      eventType: "finding.enriched",
      correlationId: "corr-a1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail:
        "Owner Payments Platform (High confidence), Production, Restricted, source drift likely",
      createdAt: "2026-07-09T10:00:07Z",
    },
    {
      eventId: "ev-003",
      violationId: "POL-001",
      eventType: "focused_agent.signals_detected",
      correlationId: "corr-a1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail:
        "storage_public_network_access, storage_firewall_default_allow, private_endpoint_gap, source_drift_likely",
      createdAt: "2026-07-09T10:00:08Z",
    },
    {
      eventId: "ev-004",
      violationId: "POL-001",
      eventType: "risk.scored",
      correlationId: "corr-a1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Score 94, band Critical (rule risk-1.0.0)",
      createdAt: "2026-07-09T10:00:09Z",
    },
    {
      eventId: "ev-005",
      violationId: "POL-001",
      eventType: "route.planned",
      correlationId: "corr-a1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail:
        "source_pr_plus_change_ticket (rule route-1.0.0); blockers: production_runtime_change",
      createdAt: "2026-07-09T10:00:10Z",
    },
    {
      eventId: "ev-006",
      violationId: "POL-001",
      eventType: "approval.requested",
      correlationId: "corr-a2",
      actionId: "apr-7781",
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Approver role: Cloud Governance Approver",
      createdAt: "2026-07-09T11:55:00Z",
    },
    {
      eventId: "ev-007",
      violationId: "POL-001",
      eventType: "approval.approved",
      correlationId: "corr-a2",
      actionId: "apr-7781",
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Approved by cloudgov-approver",
      createdAt: "2026-07-09T12:10:00Z",
    },
    {
      eventId: "ev-008",
      violationId: "POL-001",
      eventType: "artifact.generated",
      correlationId: "corr-a3",
      actionId: "art-pol001-pr",
      promptRunId: "P19",
      evidencePacket: null,
      detail: "pr_comment_preview and ticket CHG-48213 (drafts)",
      createdAt: "2026-07-09T12:12:00Z",
    },
    {
      eventId: "ev-009",
      violationId: "POL-001",
      eventType: "verification.completed",
      correlationId: "corr-a4",
      actionId: "CHG-48213",
      promptRunId: "P19",
      evidencePacket:
        "evidence_packets/POL-001/verification.completed-20260709T131500.json",
      detail:
        "publicNetworkAccess Enabled -> Disabled; networkAcls.defaultAction Allow -> Deny; result Compliant",
      createdAt: "2026-07-09T13:15:00Z",
    },
  ],
  "POL-002": [
    {
      eventId: "ev-101",
      violationId: "POL-002",
      eventType: "finding.ingested",
      correlationId: "corr-b1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Ingested from azure_policy_insights export",
      createdAt: "2026-07-09T10:05:05Z",
    },
    {
      eventId: "ev-102",
      violationId: "POL-002",
      eventType: "risk.scored",
      correlationId: "corr-b1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Score 75, band High (rule risk-1.0.0)",
      createdAt: "2026-07-09T10:05:09Z",
    },
    {
      eventId: "ev-103",
      violationId: "POL-002",
      eventType: "violation.blocked",
      correlationId: "corr-b2",
      actionId: "art-pol002-blocked",
      promptRunId: "P19",
      evidencePacket: null,
      detail:
        "Blocked: missing_owner, unknown_downtime_risk, unknown_dependency_impact, production_runtime_change",
      createdAt: "2026-07-09T10:05:12Z",
    },
  ],
  "POL-003": [
    {
      eventId: "ev-201",
      violationId: "POL-003",
      eventType: "finding.ingested",
      correlationId: "corr-c1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Ingested from azure_policy_insights export",
      createdAt: "2026-07-09T10:10:05Z",
    },
    {
      eventId: "ev-202",
      violationId: "POL-003",
      eventType: "route.planned",
      correlationId: "corr-c1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "remediation_dry_run (rule route-1.0.0); no blockers",
      createdAt: "2026-07-09T10:10:10Z",
    },
    {
      eventId: "ev-203",
      violationId: "POL-003",
      eventType: "focused_agent.signals_detected",
      correlationId: "corr-c1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "purge_protection_disabled",
      createdAt: "2026-07-09T10:10:08Z",
    },
  ],
  "POL-004": [
    {
      eventId: "ev-301",
      violationId: "POL-004",
      eventType: "finding.ingested",
      correlationId: "corr-d1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Ingested from azure_policy_insights export",
      createdAt: "2026-07-09T10:15:05Z",
    },
    {
      eventId: "ev-302",
      violationId: "POL-004",
      eventType: "exception.created",
      correlationId: "corr-d2",
      actionId: "art-pol004-exception",
      promptRunId: "P19",
      evidencePacket: null,
      detail:
        "Owner Analytics Engineering, expiry 2026-08-15, compensating control: firewall logging plus weekly review",
      createdAt: "2026-07-09T10:40:00Z",
    },
  ],
  "POL-005": [
    {
      eventId: "ev-401",
      violationId: "POL-005",
      eventType: "finding.ingested",
      correlationId: "corr-e1",
      actionId: null,
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Ingested from azure_policy_insights export",
      createdAt: "2026-07-09T10:20:05Z",
    },
    {
      eventId: "ev-402",
      violationId: "POL-005",
      eventType: "violation.blocked",
      correlationId: "corr-e2",
      actionId: "art-pol005-blocked",
      promptRunId: "P19",
      evidencePacket: null,
      detail: "Blocked: missing_owner and three further safety blockers",
      createdAt: "2026-07-09T10:20:12Z",
    },
  ],
};
