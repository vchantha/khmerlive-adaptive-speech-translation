from pydantic import BaseModel, Field

class UrlIngestRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    source_name: str | None = Field(default=None, max_length=255)

class StreamIngestRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    source_name: str = Field(default="KhmerLive Live", min_length=1, max_length=255)
