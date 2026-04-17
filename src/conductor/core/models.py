"""Data models for platform-conductor."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class WorkflowRun(BaseModel):
    """A single GitHub Actions workflow run."""

    repo: str
    workflow: str
    status: str
    conclusion: str = ""
    run_id: int = 0
    created_at: str = ""
    html_url: str = ""

    @property
    def succeeded(self) -> bool:
        return self.conclusion == "success"

    @property
    def failed(self) -> bool:
        return self.conclusion in ("failure", "timed_out", "cancelled")

    @property
    def is_agent(self) -> bool:
        return "nightly" in self.workflow.lower() or "agent" in self.workflow.lower()


class RepoHealth(BaseModel):
    """Health status for a single repository."""

    repo: str
    last_agent_run: Optional[str] = None
    agent_succeeded: bool = False
    ci_succeeded: bool = False
    open_issues: int = 0
    health_score: int = 0
    status: str = "unknown"


class PlatformHealth(BaseModel):
    """Aggregated health across all portfolio repos."""

    checked_at: str = ""
    total_repos: int = 0
    healthy_repos: int = 0
    failed_repos: int = 0
    skipped_repos: int = 0
    platform_score: int = 0
    repo_health: list[RepoHealth] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    weekly_narrative: str = ""

    @property
    def health_pct(self) -> float:
        if self.total_repos == 0:
            return 0.0
        return round(self.healthy_repos / self.total_repos * 100, 1)