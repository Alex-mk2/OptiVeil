from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .database import Base
from sqlalchemy.orm import relationship

# JSONB en PostgreSQL (producción); JSON genérico en otros motores (p. ej.
# sqlite en los tests). Mantiene el rendimiento de JSONB sin bloquear los tests.
JSONType = JSON().with_variant(JSONB(), "postgresql")

class AuditScan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    stealth_level = Column(Integer)
    best_config = Column(JSONType)
    findings = Column(JSONType)
    attack_roadmap = Column(JSONType)
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
    result = Column(JSONType)
    error = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

