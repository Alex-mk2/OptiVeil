from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .database import Base
from sqlalchemy.orm import relationship

class AuditScan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    stealth_level = Column(Integer)
    best_config = Column(JSONB)
    findings = Column(JSONB)
    attack_roadmap = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    scan_hash = Column(String, unique=True, index=True)


class ScanJob(Base):
    """Estado de un escaneo ejecutado en background para no bloquear la API."""
    __tablename__ = "scan_jobs"
    id = Column(String, primary_key=True, index=True)
    target = Column(String, index=True)
    stealth_level = Column(Integer)
    ports = Column(Integer)
    status = Column(String, default="pending", index=True)  # pending | running | done | error
    result = Column(JSONB)
    error = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

