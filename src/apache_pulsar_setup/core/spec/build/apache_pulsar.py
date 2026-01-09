from typing import List

from pydantic import BaseModel, Field


class JavaConfig(BaseModel):
    Major: str
    Minor: str
    Build: str


class JavaJreConfig(BaseModel):
    Jre: JavaConfig = Field(default_factory=JavaConfig)


class RuntimeConfig(BaseModel):
    Dependencies: List[str] = Field(default_factory=list)
    Resources: str = "resources"
    Uid: int = 1002
    Gid: int = 1002
    PulsarGc: List[str] = Field(default_factory=list)
    Java: JavaJreConfig = Field(default_factory=JavaJreConfig)
    Ports: List[int] = Field(default_factory=list)


class BuildConfig(BaseModel):
    Dependencies: List[str] = Field(default_factory=list)
    Flags: List[str] = Field(default_factory=list)


class ApachePulsarConfig(BaseModel):
    Version: str
    SourceUrl: str
    Prefix: str = '/usr/local/pulsar'
    Build: BuildConfig = Field(default_factory=BuildConfig)
    Runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

