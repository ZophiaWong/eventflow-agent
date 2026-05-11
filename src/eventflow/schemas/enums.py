"""Shared enums for EventFlow Agent schemas."""

from enum import StrEnum


class EventType(StrEnum):
    """Supported M1 external event types."""

    SERVICE_INCIDENT = "service_incident"
    SECURITY_ADVISORY = "security_advisory"
    API_CHANGE = "api_change"
    PRODUCT_RELEASE = "product_release"


class SourceType(StrEnum):
    """Supported source categories for raw signals."""

    STATUS_PAGE = "status_page"
    RELEASE_NOTE = "release_note"
    SECURITY_ADVISORY = "security_advisory"
    VENDOR_BLOG = "vendor_blog"
    GITHUB_RELEASE = "github_release"
    RSS = "rss"
    MANUAL = "manual"


class RiskLevel(StrEnum):
    """Risk and dependency criticality levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendedAction(StrEnum):
    """Allowed MVP recommended actions."""

    IGNORE = "ignore"
    WATCH = "watch"
    NOTIFY_SUPPORT = "notify_support"
    CREATE_INTERNAL_ISSUE = "create_internal_issue"
    ESCALATE_TO_ENGINEERING = "escalate_to_engineering"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"


class ReviewStatus(StrEnum):
    """Allowed review states."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    REQUESTED_MORE_EVIDENCE = "requested_more_evidence"


class ExpectedRoute(StrEnum):
    """Allowed replay evaluation routes."""

    AUTO_BRIEF = "auto_brief"
    HUMAN_REVIEW = "human_review"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"
    ERROR = "error"


class LabelStatus(StrEnum):
    """Eval label review status."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
