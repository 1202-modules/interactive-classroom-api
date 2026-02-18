"""Module settings validation utilities."""
from typing import Dict, Any, Optional, Literal

from pydantic import BaseModel, Field

from models.workspace_module import ModuleType


def validate_module_settings(module_type: str, settings: Optional[Dict[str, Any]]) -> None:
    """
    Validate module settings based on module type.

    Args:
        module_type: Type of module (quiz, poll, questions, timer)
        settings: Settings dictionary to validate

    Raises:
        ValueError: If settings are invalid
    """
    if settings is None:
        settings = {}

    if not isinstance(settings, dict):
        raise ValueError("Settings must be a dictionary")

    if module_type == ModuleType.QUIZ.value:
        validate_quiz_settings(settings)
    elif module_type == ModuleType.POLL.value:
        validate_poll_settings(settings)
    elif module_type == ModuleType.QUESTIONS.value:
        validate_questions_settings(settings)
    elif module_type == ModuleType.TIMER.value:
        validate_timer_settings(settings)
    else:
        raise ValueError(f"Unknown module type: {module_type}")


def validate_quiz_settings(settings: Dict[str, Any]) -> None:
    """
    Validate Quiz module settings.

    Args:
        settings: Quiz settings dictionary

    Raises:
        ValueError: If settings are invalid
    """
    # Quiz settings structure:
    # {
    #   "question": str,
    #   "options": [{"text": str, "is_correct": bool}],
    #   "timer_seconds": int (optional),
    #   ...
    # }
    pass  # Basic validation - can be extended later


def validate_poll_settings(settings: Dict[str, Any]) -> None:
    """
    Validate Poll module settings.

    Args:
        settings: Poll settings dictionary

    Raises:
        ValueError: If settings are invalid
    """
    # Poll settings structure:
    # {
    #   "question": str,
    #   "options": [str] (optional),
    #   ...
    # }
    pass  # Basic validation - can be extended later


# Questions: length limit modes and character limits
QUESTIONS_LENGTH_LIMIT_MODES = ("compact", "moderate", "extended")
QUESTIONS_LENGTH_LIMITS: Dict[str, int] = {
    "compact": 100,
    "moderate": 250,
    "extended": 500,
}


class QuestionsModuleSettings(BaseModel):
    """
    Questions module settings schema.
    Defaults are applied via Field(default=...).
    """

    length_limit_mode: Literal["compact", "moderate", "extended"] = Field(
        default="moderate",
        description="Character limit mode",
    )
    likes_enabled: bool = Field(default=True, description="Allow participants to like questions")
    allow_anonymous: bool = Field(
        default=False,
        description="Allow participants to submit questions semi-anonymously (lecturer still sees author in Inspect)",
    )
    cooldown_enabled: bool = Field(default=False, description="Cooldown between participant questions")
    cooldown_seconds: int = Field(default=30, ge=0, description="Cooldown duration in seconds")
    allow_participant_answers: bool = Field(default=True, description="Allow lecturer to enable participant answers")
    max_questions_total: Optional[int] = Field(
        default=None,
        gt=0,
        description="Max total questions, None = unlimited",
    )

    model_config = {"extra": "allow"}

    def get_max_length(self) -> int:
        return QUESTIONS_LENGTH_LIMITS.get(
            self.length_limit_mode,
            QUESTIONS_LENGTH_LIMITS["moderate"],
        )


class TimerModuleSettings(BaseModel):
    """
    Timer module settings schema.
    Defaults are applied via Field(default=...).
    """

    duration_seconds: int = Field(default=60, gt=0, description="Timer duration in seconds")
    sound_notification_enabled: bool = Field(default=True, description="Play sound when timer ends")

    model_config = {"extra": "allow"}


def validate_questions_settings(settings: Dict[str, Any]) -> None:
    """
    Validate Questions module settings.

    Raises:
        ValueError: If settings are invalid
    """
    try:
        QuestionsModuleSettings.model_validate(settings or {})
    except Exception as e:
        raise ValueError(f"Invalid questions settings: {e}") from e


def validate_timer_settings(settings: Dict[str, Any]) -> None:
    """
    Validate Timer module settings.

    Raises:
        ValueError: If settings are invalid
    """
    try:
        TimerModuleSettings.model_validate(settings or {})
    except Exception as e:
        raise ValueError(f"Invalid timer settings: {e}") from e


def get_questions_settings(settings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return Questions module settings with defaults applied (as dict)."""
    return QuestionsModuleSettings.model_validate(settings or {}).model_dump()


def get_questions_max_length(opts: Dict[str, Any]) -> int:
    """Get max character limit from Questions settings."""
    parsed = QuestionsModuleSettings.model_validate(opts)
    return parsed.get_max_length()


def get_timer_settings(settings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return Timer module settings with defaults applied (as dict)."""
    return TimerModuleSettings.model_validate(settings or {}).model_dump()
