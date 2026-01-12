"""Email sending utility for verification codes."""
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from core.config import settings
import structlog

logger = structlog.get_logger(__name__)


def generate_verification_code(length: int = None) -> str:
    """Generate random verification code."""
    if length is None:
        length = settings.VERIFICATION_CODE_LENGTH
    return ''.join(random.choices(string.digits, k=length))


def send_verification_email(email: str, code: str) -> bool:
    """
    Send verification code to email.
    
    Args:
        email: Recipient email address
        code: Verification code to send
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.SMTP_FROM_EMAIL]):
        logger.warning("Email configuration not set, skipping email send", email=email)
        # In development, just log the code
        logger.info("Verification code (dev mode)", email=email, code=code)
        return True
    
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "Email Verification Code"
        
        body = f"""
        Your verification code is: {code}
        
        This code will expire in {settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info("Verification email sent", email=email)
        return True
    except Exception as e:
        logger.error("Failed to send verification email", email=email, error=str(e), exc_info=True)
        return False

