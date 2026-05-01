"""Configuration for platform-conductor."""

from __future__ import annotations

import os
from pydantic import BaseModel, Field


PORTFOLIO_REPOS = [
    "repoforge", "pr-autopilot", "runbook-gen",
    "mcp-incident-intel", "mcp-compliance-grc", "mcp-developer-portal",
    "TeamHealthRadar", "PlatformSLOBoard", "TechDebtLedger",
    "IncidentPilot", "DataPipelineAgent", "BoardroomBrief",
    "innersource-scorecard", "service-catalog-sync", "platform-maturity-model",
]

GITHUB_ORG = "brianpelow"


class ConductorConfig(BaseModel):
    """Runtime configuration for platform-conductor."""

    github_token: str = Field("", description="GitHub API token")
    openrouter_api_key: str = Field("", description="OpenRouter API key")
    org: str = Field(GITHUB_ORG, description="GitHub organization")
    repos: list[str] = Field(default_factory=lambda: PORTFOLIO_REPOS)
    industry: str = Field("fintech", description="Industry context")

    @classmethod
    def from_env(cls) -> "ConductorConfig":
        return cls(
            github_token=os.environ.get("GITHUB_TOKEN", ""),
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        )

    @property
    def has_github(self) -> bool:
        return bool(self.github_token)

    @property
    def has_api_key(self) -> bool:
        return bool(self.openrouter_api_key)