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

