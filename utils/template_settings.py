"""Template settings (Session defaults) validation utilities."""
from typing import Literal, Optional, Dict, Any

from pydantic import BaseModel, Field


ParticipantEntryMode = Literal["anonymous", "registered", "sso", "email_code"]


class TemplateSettings(BaseModel):
    """
    Session defaults (template_settings) schema for workspace.

    These settings are applied to new sessions in the workspace.
    Sessions can override individual values via custom_settings.
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

    model_config = {"extra": "allow"}


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
