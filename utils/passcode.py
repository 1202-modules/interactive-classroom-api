"""Passcode generation and validation utilities."""
import random
import string
from typing import Optional
from sqlalchemy.orm import Session
from models.session import Session as SessionModel


def generate_passcode(length: int = 6) -> str:
    """
    Generate a random alphanumeric passcode.
    
    Args:
        length: Length of passcode (default: 6)
    
    Returns:
        Random alphanumeric string
    """
    # Use uppercase letters and digits for better readability
    characters = string.ascii_uppercase + string.digits
    # Exclude confusing characters: 0, O, 1, I
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    return ''.join(random.choices(characters, k=length))


def generate_unique_passcode(db: Session, max_attempts: int = 100) -> str:
    """
    Generate a unique passcode that doesn't exist in the database.
    
    Args:
        db: Database session
        max_attempts: Maximum number of attempts to generate unique passcode
    
    Returns:
        Unique passcode
    
    Raises:
        ValueError: If unable to generate unique passcode after max_attempts
    """
    for _ in range(max_attempts):
        passcode = generate_passcode()
        # Check if passcode already exists (including deleted sessions)
        existing = db.query(SessionModel).filter(
            SessionModel.passcode == passcode
        ).first()
        if not existing:
            return passcode
    
    raise ValueError(f"Unable to generate unique passcode after {max_attempts} attempts")


def validate_passcode_format(passcode: str) -> bool:
    """
    Validate passcode format.
    
    Args:
        passcode: Passcode to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not passcode:
        return False
    if len(passcode) != 6:
        return False
    # Check if all characters are alphanumeric (excluding confusing chars)
    valid_chars = set(string.ascii_uppercase + string.digits)
    valid_chars.discard('0')
    valid_chars.discard('O')
    valid_chars.discard('1')
    valid_chars.discard('I')
    return all(c in valid_chars for c in passcode)

