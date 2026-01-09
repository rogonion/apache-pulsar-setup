from pydantic import BaseModel, Field

from .apache_pulsar import ApachePulsarConfig
from .postgres_sink import PostgresSinkConfig


class BuildahConfig(BaseModel):
    Path: str = 'buildah'


class BuildSpec(BaseModel):
    ProjectName: str
    BaseImage: str
    Buildah: BuildahConfig = Field(default_factory=BuildahConfig)
    ApachePulsar: ApachePulsarConfig = Field(default_factory=ApachePulsarConfig)
    PostgresSink: PostgresSinkConfig = Field(default_factory=PostgresSinkConfig)
