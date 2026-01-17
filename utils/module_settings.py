"""Module settings validation utilities."""
from typing import Dict, Any, Optional
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
    
    # Basic validation for each module type
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
    #   "show_explanation": bool (optional),
    #   "explanation": str (optional),
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
    #   "allow_custom_answers": bool (optional),
    #   ...
    # }
    pass  # Basic validation - can be extended later


def validate_questions_settings(settings: Dict[str, Any]) -> None:
    """
    Validate Questions module settings.
    
    Args:
        settings: Questions settings dictionary
    
    Raises:
        ValueError: If settings are invalid
    """
    # Questions settings structure:
    # {
    #   "allow_participant_answers": bool (optional),
    #   "max_answer_length": int (optional),
    #   "cooldown_seconds": int (optional),
    #   ...
    # }
    pass  # Basic validation - can be extended later


def validate_timer_settings(settings: Dict[str, Any]) -> None:
    """
    Validate Timer module settings.
    
    Args:
        settings: Timer settings dictionary
    
    Raises:
        ValueError: If settings are invalid
    """
    # Timer settings structure:
    # {
    #   "duration_seconds": int,
    #   "show_notification": bool (optional),
    #   ...
    # }
    if "duration_seconds" in settings:
        duration = settings["duration_seconds"]
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError("duration_seconds must be a positive integer")

