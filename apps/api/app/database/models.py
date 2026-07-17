import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, ForeignKey, DateTime, JSON, Boolean, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_username: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="local", nullable=False) # local, github
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    settings: Mapped["Settings"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    github_account: Mapped["GitHubAccount"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    repositories: Mapped[List["Repository"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User email={self.email} username={self.username}>"


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="settings")


class GitHubAccount(Base):
    __tablename__ = "github_accounts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    github_user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    github_username: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    access_token: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="github_account")


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    visibility: Mapped[str] = mapped_column(String(50), default="public", nullable=False) # public, private
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    languages: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    clone_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # in KB
    last_commit_hash: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_commit_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    import_method: Mapped[str] = mapped_column(String(50), nullable=False) # github, upload
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="repositories")
    settings: Mapped["RepositorySettings"] = relationship(back_populates="repository", cascade="all, delete-orphan", uselist=False)
    imports: Mapped[List["RepositoryImport"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    tags: Mapped[List["RepositoryTag"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    folders: Mapped[List["RepositoryFolder"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    files: Mapped[List["RepositoryFile"]] = relationship(back_populates="repository", cascade="all, delete-orphan")
    statistics: Mapped["AnalysisStatistics"] = relationship(back_populates="repository", cascade="all, delete-orphan", uselist=False)


class RepositoryImport(Base):
    __tablename__ = "repository_imports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False) # queued, running, completed, failed
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="imports")


class RepositorySettings(Base):
    __tablename__ = "repository_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_auto_sync: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sync_interval_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="settings")


class RepositoryTag(Base):
    __tablename__ = "repository_tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    tag_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="tags")


class RepositoryFolder(Base):
    __tablename__ = "repository_folders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("repository_folders.id", ondelete="CASCADE"), nullable=True)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # total folder size in KB

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="folders")
    files: Mapped[List["RepositoryFile"]] = relationship(back_populates="folder", cascade="all, delete-orphan")


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    folder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repository_folders.id", ondelete="CASCADE"), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # file size in KB
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    hash: Mapped[str] = mapped_column(String(100), nullable=False) # SHA-256 hash for diff check
    content_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="files")
    folder: Mapped["RepositoryFolder"] = relationship(back_populates="files")
    symbols: Mapped[List["Symbol"]] = relationship(back_populates="file", cascade="all, delete-orphan")
    imports: Mapped[List["Import"]] = relationship(back_populates="file", cascade="all, delete-orphan")


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False) # class, function, variable, interface
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[int] = mapped_column(Integer, nullable=False)
    code_snippet: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    docstring: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    file: Mapped["RepositoryFile"] = relationship(back_populates="symbols")
    class_details: Mapped["Class"] = relationship(back_populates="symbol", cascade="all, delete-orphan", uselist=False)
    function_details: Mapped["Function"] = relationship(back_populates="symbol", cascade="all, delete-orphan", uselist=False)


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    symbol_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), unique=True, nullable=False)
    inheritance_list: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    symbol: Mapped["Symbol"] = relationship(back_populates="class_details")


class Function(Base):
    __tablename__ = "functions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    symbol_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), unique=True, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=list, nullable=False) # list of parameter details
    return_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decorator_list: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    symbol: Mapped["Symbol"] = relationship(back_populates="function_details")


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    source_module: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_symbols: Mapped[dict] = mapped_column(JSON, default=list, nullable=False) # imported functions/classes list
    is_external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    file: Mapped["RepositoryFile"] = relationship(back_populates="imports")


class Dependency(Base):
    __tablename__ = "dependencies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    target_file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    dependency_type: Mapped[str] = mapped_column(String(50), default="imports", nullable=False) # imports, calls


class API(Base):
    __tablename__ = "apis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    route: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False) # GET, POST, etc
    parameters: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    controller_func: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DatabaseModel(Base):
    __tablename__ = "database_models"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    fields_json: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    relationships_json: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)


class AnalysisStatistics(Base):
    __tablename__ = "analysis_statistics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), unique=True, nullable=False)
    loc: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    folders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    languages_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    frameworks_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="statistics")


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(sa_fk := ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False) # folder, file, class, function, api, model
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(50), nullable=False) # IMPORTS, CALLS, INHERITS, USES, ROUTES_TO
    strength: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class SearchHistory(Base):
    __tablename__ = "search_histories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False) # user, assistant
    content: Mapped[str] = mapped_column(String, nullable=False)
    citations_json: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AISetting(Base):
    __tablename__ = "ai_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(100), default="openai", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class WorkspaceState(Base):
    __tablename__ = "workspace_states"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    active_layout: Mapped[str] = mapped_column(String(50), default="spiral", nullable=False)
    zoom: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    pan_x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pan_y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    active_filters_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), nullable=False)
    note_type: Mapped[str] = mapped_column(String(50), nullable=False) # file, symbol, node
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    view_state_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Documentation(Base):
    __tablename__ = "documentations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False) # README, architecture, api, developer_guide
    content: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class EngineeringReport(Base):
    __tablename__ = "engineering_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False) # health, impact, summary
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DocumentationTemplate(Base):
    __tablename__ = "documentation_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False) # quality, security, architecture, performance
    severity: Mapped[str] = mapped_column(String(50), default="warning", nullable=False) # info, warning, critical
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    thresholds_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), nullable=False) # file_id or symbol_name
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False) # open, resolved, suppressed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class HealthScore(Base):
    __tablename__ = "health_scores"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    overall: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    quality: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    security: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    architecture: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False) # owner, admin, member
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    target_url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret_token: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
