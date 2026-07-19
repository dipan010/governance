"""Explicit enum values for the canonical evidence schema.

RULES.md backend rule 3: use explicit enum values for severity, environment,
route, status, blocker, approval state, and verification result.
"""

from enum import StrEnum


class Severity(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class ComplianceState(StrEnum):
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "NonCompliant"
    UNKNOWN = "Unknown"


class EnvironmentType(StrEnum):
    PRODUCTION = "Production"
    STAGING = "Staging"
    DEVELOPMENT = "Development"
    UNKNOWN = "Unknown"


class DataClassification(StrEnum):
    RESTRICTED = "Restricted"
    CONFIDENTIAL = "Confidential"
    INTERNAL = "Internal"
    PUBLIC = "Public"
    UNKNOWN = "Unknown"


class ConfidenceLevel(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class RiskBand(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RoutePath(StrEnum):
    SOURCE_PR_PLUS_CHANGE_TICKET = "source_pr_plus_change_ticket"
    REMEDIATION_DRY_RUN = "remediation_dry_run"
    OWNER_TICKET_OR_CHANGE_REQUEST = "owner_ticket_or_change_request"
    TIME_BOUND_EXCEPTION = "time_bound_exception"
    BLOCKED_MANUAL_REVIEW = "blocked_manual_review"
    ESCALATION = "escalation"
    OBSERVE = "observe"
    INVALID_FINDING = "invalid_finding"


class BlockerCode(StrEnum):
    MISSING_OWNER = "missing_owner"
    MISSING_RESOURCE_IDENTITY = "missing_resource_identity"
    MISSING_FAILURE_REASON = "missing_failure_reason"
    MISSING_VERIFICATION_QUERY = "missing_verification_query"
    UNKNOWN_DOWNTIME_RISK = "unknown_downtime_risk"
    UNKNOWN_DEPENDENCY_IMPACT = "unknown_dependency_impact"
    PRODUCTION_RUNTIME_CHANGE = "production_runtime_change"
    MISSING_PERMISSION_CHECK = "missing_permission_check"
    SOURCE_CODE_CHANGE_WITHOUT_APPROVAL = "source_code_change_without_approval"
    EXCEPTION_WITHOUT_EXPIRY = "exception_without_expiry"


class FocusedSignal(StrEnum):
    # Storage Firewall Compliance Agent
    STORAGE_PUBLIC_NETWORK_ACCESS = "storage_public_network_access"
    STORAGE_FIREWALL_DEFAULT_ALLOW = "storage_firewall_default_allow"
    PRIVATE_ENDPOINT_GAP = "private_endpoint_gap"
    SOURCE_DRIFT_LIKELY = "source_drift_likely"
    # NSG Drift Management Agent
    BROAD_SOURCE_CIDR = "broad_source_cidr"
    SENSITIVE_PORT_EXPOSED = "sensitive_port_exposed"
    PRIORITY_DRIFT = "priority_drift"


class PolicyEffect(StrEnum):
    AUDIT = "Audit"
    DENY = "Deny"
    MODIFY = "Modify"
    DEPLOY_IF_NOT_EXISTS = "DeployIfNotExists"
    AUDIT_IF_NOT_EXISTS = "AuditIfNotExists"
    APPEND = "Append"
    DISABLED = "Disabled"


class ImpactLevel(StrEnum):
    """Restart, downtime, and cost impact levels. Unknown blocks auto-action."""

    NONE = "None"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    UNKNOWN = "Unknown"


class ActionStatus(StrEnum):
    OPEN = "Open"
    AWAITING_APPROVAL = "AwaitingApproval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ARTIFACT_CREATED = "ArtifactCreated"
    VERIFICATION_PENDING = "VerificationPending"
    VERIFIED = "Verified"
    CLOSED = "Closed"
    BLOCKED = "Blocked"


class ApprovalState(StrEnum):
    NOT_REQUESTED = "NotRequested"
    REQUESTED = "Requested"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    DEFERRED = "Deferred"


class VerificationResult(StrEnum):
    NOT_RUN = "NotRun"
    COMPLIANT = "Compliant"
    FAILED = "Failed"
