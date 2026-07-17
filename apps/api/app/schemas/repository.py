import uuid
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class RepositoryGitHubImport(BaseModel):
    clone_url: str = Field(..., description="The GitHub repository HTTPS URL to clone")


class RepositoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    is_auto_sync: bool | None = None
    sync_interval_hours: int | None = Field(None, ge=1)
    tags: list[str] | None = None


class RepositoryTagResponse(BaseModel):
    tag_name: str

    class Config:
        from_attributes = True


class RepositorySettingsResponse(BaseModel):
    is_auto_sync: bool
    sync_interval_hours: int

    class Config:
        from_attributes = True


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner: str
    description: str | None
    visibility: str
    default_branch: str
    languages: dict
    clone_url: str | None
    local_path: str
    size: int
    last_commit_hash: str | None
    last_commit_message: str | None
    last_commit_at: datetime | None
    import_method: str
    created_at: datetime
    updated_at: datetime
    settings: RepositorySettingsResponse | None = None
    tags: list[RepositoryTagResponse] = []
    import_status: str | None = None # queued, running, completed, failed
    import_progress: float = 0.0

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
