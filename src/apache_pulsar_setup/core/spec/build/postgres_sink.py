from typing import List, Dict

from pydantic import BaseModel, Field

class VersionsConfig(BaseModel):
    SourceUrl: str
    Dependencies: List[str] = Field(default_factory=list)
    Uid: int
    Gid: int

class PostgresSinkConfig(BaseModel):
    Current: str
    ConfigPath: str
    BrokerUrl: str
    Versions: Dict[str, VersionsConfig] = Field(default_factory=list)
