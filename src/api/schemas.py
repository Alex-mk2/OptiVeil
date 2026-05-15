from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyAddress
from typing import List




class ScanRequest(BaseModel):
    target: IPvAnyAddress = Field(..., example="186.64.114.50")
    stealth: int = Field(5, ge=1, le=10)
    ports: int = Field(100, ge=1)
    
    
class NmapFinding(BaseModel):
    port: int
    service: str
    banner: str


class LiveStrategyRequest(BaseModel):
    target: str
    stealth: int
    findings: list[NmapFinding]