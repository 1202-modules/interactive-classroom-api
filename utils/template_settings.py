"""Template settings (Session defaults) validation utilities."""
from typing import Literal, Optional, Dict, Any, List

from pydantic import BaseModel, Field, field_validator, model_validator


ParticipantEntryMode = Literal["anonymous", "registered", "sso", "email_code"]


def _normalize_domains_whitelist(v: Optional[List[str]]) -> Optional[List[str]]:
    """Normalize whitelist: lowercase, strip, filter empty. None or empty = any domain allowed."""
    if v is None:
        return None
    if not isinstance(v, list):
        return v
    normalized = [s.strip().lower() for s in v if isinstance(s, str) and s.strip()]
    return normalized if normalized else None


class TemplateSettings(BaseModel):
    """
    Session defaults (template_settings) schema for workspace.

    These settings are applied to new sessions in the workspace.
    New sessions get a full copy of these settings at creation (session.settings).
    """

    default_session_duration_min: Optional[int] = Field(
        default=90,
        ge=5,
        le=420,
        description="Default session duration in minutes (5-420)",
    )
    max_participants: Optional[int] = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum participants per session (1-500)",
    )
    participant_entry_mode: Optional[ParticipantEntryMode] = Field(
        default="anonymous",
        description="How guests join the session: anonymous, registered, sso, email_code",
    )
    email_code_domains_whitelist: Optional[List[str]] = Field(
        default=None,
        description="Allowed email domains for email_code entry mode. Empty or missing = any domain.",
    )
    sso_organization_id: Optional[int] = Field(
        default=None,
        description="Organization ID for SSO entry mode. Required when participant_entry_mode is sso.",
    )

    model_config = {"extra": "allow"}

    @field_validator("email_code_domains_whitelist", mode="before")
    @classmethod
    def normalize_email_code_domains_whitelist(cls, v: Any) -> Optional[List[str]]:
        return _normalize_domains_whitelist(v)

    @model_validator(mode="after")
    def sso_requires_organization_id(self) -> "TemplateSettings":
        if self.participant_entry_mode == "sso" and not self.sso_organization_id:
            raise ValueError("sso_organization_id is required when participant_entry_mode is sso")
        return self


def validate_template_settings(template_settings: Optional[Dict[str, Any]]) -> None:
    """
    Validate template_settings against the TemplateSettings schema.

    Known fields are validated; unknown fields are allowed (for future WIP features).

    Args:
        template_settings: Template settings dictionary (Session defaults)

    Raises:
        ValueError: If template_settings is invalid
    """
    if template_settings is None:
        return

    if not isinstance(template_settings, dict):
        raise ValueError("template_settings must be a dictionary")

    try:
        TemplateSettings.model_validate(template_settings)
    except Exception as e:
        raise ValueError(f"Invalid template_settings: {e}") from e
