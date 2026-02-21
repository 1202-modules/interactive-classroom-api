"""Repository for session join fingerprint tracking."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.session_join_fingerprint import SessionJoinFingerprint
from models.session_participant import SessionParticipant


class SessionJoinFingerprintRepository:
    """CRUD helpers for join-fingerprint records."""

    @staticmethod
    def count_since(
        db: DBSession,
        session_id: int,
        fingerprint_hash: str,
        entry_type: str,
        created_after: datetime,
    ) -> int:
        """Count join records in rolling window for active (not kicked) participants."""
        return (
            db.query(SessionJoinFingerprint)
            .join(
                SessionParticipant,
                SessionParticipant.id == SessionJoinFingerprint.participant_id,
            )
            .filter(
                SessionJoinFingerprint.session_id == session_id,
                SessionJoinFingerprint.fingerprint_hash == fingerprint_hash,
                SessionJoinFingerprint.entry_type == entry_type,
                SessionJoinFingerprint.created_at >= created_after,
                SessionParticipant.is_deleted == False,
            )
            .count()
        )

    @staticmethod
    def create(
        db: DBSession,
        session_id: int,
        fingerprint_hash: str,
        entry_type: str,
        participant_id: Optional[int] = None,
    ) -> SessionJoinFingerprint:
        """Create join record without commit."""
        rec = SessionJoinFingerprint(
            session_id=session_id,
            participant_id=participant_id,
            fingerprint_hash=fingerprint_hash,
            entry_type=entry_type,
        )
        db.add(rec)
        return rec
