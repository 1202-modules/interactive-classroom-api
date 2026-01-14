"""PendingRegistration repository for database operations."""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from models.pending_registration import PendingRegistration


class PendingRegistrationRepository:
    """Repository for pending registration operations."""
    
    @staticmethod
    def create(
        db: Session,
        email: str,
        password_hash: str,
        verification_code: str,
        verification_code_expires_at: datetime
    ) -> PendingRegistration:
        """
        Create a new pending registration.
        
        Args:
            db: Database session
            email: User email
            password_hash: Hashed password
            verification_code: Verification code
            verification_code_expires_at: Code expiration datetime
        
        Returns:
            Created PendingRegistration instance
        """
        pending_reg = PendingRegistration(
            email=email,
            password_hash=password_hash,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at
        )
        db.add(pending_reg)
        db.commit()
        db.refresh(pending_reg)
        return pending_reg
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[PendingRegistration]:
        """
        Get pending registration by email.
        
        Args:
            db: Database session
            email: User email
        
        Returns:
            PendingRegistration instance or None
        """
        return db.query(PendingRegistration).filter(
            PendingRegistration.email == email
        ).first()
    
    @staticmethod
    def get_by_email_and_code(
        db: Session,
        email: str,
        code: str
    ) -> Optional[PendingRegistration]:
        """
        Get pending registration by email and verification code.
        
        Args:
            db: Database session
            email: User email
            code: Verification code
        
        Returns:
            PendingRegistration instance or None
        """
        return db.query(PendingRegistration).filter(
            PendingRegistration.email == email,
            PendingRegistration.verification_code == code
        ).first()
    
    @staticmethod
    def delete(db: Session, pending_reg_id: int) -> bool:
        """
        Delete a pending registration.
        
        Args:
            db: Database session
            pending_reg_id: Pending registration ID
        
        Returns:
            True if deleted, False if not found
        """
        pending_reg = db.query(PendingRegistration).filter(
            PendingRegistration.id == pending_reg_id
        ).first()
        
        if pending_reg:
            db.delete(pending_reg)
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_by_email(db: Session, email: str) -> bool:
        """
        Delete pending registration by email.
        
        Args:
            db: Database session
            email: User email
        
        Returns:
            True if deleted, False if not found
        """
        pending_reg = PendingRegistrationRepository.get_by_email(db, email)
        if pending_reg:
            db.delete(pending_reg)
            db.commit()
            return True
        return False
    
    @staticmethod
    def delete_expired(db: Session) -> int:
        """
        Delete expired pending registrations.
        
        Args:
            db: Database session
        
        Returns:
            Number of registrations deleted
        """
        now = datetime.now(timezone.utc)
        count = db.query(PendingRegistration).filter(
            PendingRegistration.verification_code_expires_at < now
        ).delete()
        db.commit()
        return count
    
    @staticmethod
    def update_verification_code(
        db: Session,
        email: str,
        verification_code: str,
        verification_code_expires_at: datetime
    ) -> Optional[PendingRegistration]:
        """
        Update verification code for pending registration.
        
        Args:
            db: Database session
            email: User email
            verification_code: New verification code
            verification_code_expires_at: New expiration datetime
        
        Returns:
            Updated PendingRegistration instance or None
        """
        pending_reg = PendingRegistrationRepository.get_by_email(db, email)
        if not pending_reg:
            return None
        
        pending_reg.verification_code = verification_code
        pending_reg.verification_code_expires_at = verification_code_expires_at
        db.commit()
        db.refresh(pending_reg)
        return pending_reg

