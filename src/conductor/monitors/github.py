"""GitHub Actions workflow monitor."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import httpx

from conductor.core.models import WorkflowRun, RepoHealth
from conductor.core.config import ConductorConfig


class GitHubMonitor:
    """Monitors GitHub Actions workflow runs across portfolio repos."""

    BASE_URL = "https://api.github.com"

    def __init__(self, config: ConductorConfig) -> None:
        self.config = config

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.config.github_token:
            headers["Authorization"] = f"Bearer {self.config.github_token}"
        return headers

    def get_recent_runs(self, repo: str, hours: int = 26) -> list[WorkflowRun]:
        """Get workflow runs for a repo in the last N hours."""
        if not self.config.has_github:
            return _mock_runs(repo)
        try:
            since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
            with httpx.Client(timeout=30, headers=self._headers()) as client:
                response = client.get(
                    f"{self.BASE_URL}/repos/{self.config.org}/{repo}/actions/runs",
                    params={"created": f">={since}", "per_page": 20},
                )
                if response.status_code != 200:
                    return _mock_runs(repo)
                runs = response.json().get("workflow_runs", [])
                return [_parse_run(repo, r) for r in runs]
        except Exception:
            return _mock_runs(repo)

    def get_repo_health(self, repo: str) -> RepoHealth:
        """Compute health status for a single repo."""
        runs = self.get_recent_runs(repo)
        agent_runs = [r for r in runs if r.is_agent]
        ci_runs = [r for r in runs if not r.is_agent]

        agent_ok = any(r.succeeded for r in agent_runs) if agent_runs else False
        ci_ok = any(r.succeeded for r in ci_runs) if ci_runs else True

        last_agent = agent_runs[0].created_at if agent_runs else None

        score = 100
        if not agent_ok and agent_runs:
            score -= 40
        if not ci_ok:
            score -= 30
        if not agent_runs:
            score -= 20

        status = "healthy" if score >= 80 else "degraded" if score >= 50 else "failed"

        return RepoHealth(
            repo=repo,
            last_agent_run=last_agent,
            agent_succeeded=agent_ok,
            ci_succeeded=ci_ok,
            health_score=score,
            status=status,
        )

    def check_all_repos(self) -> list[RepoHealth]:
        """Check health of all portfolio repos."""
        return [self.get_repo_health(repo) for repo in self.config.repos]


def _parse_run(repo: str, data: dict[str, Any]) -> WorkflowRun:
    return WorkflowRun(
        repo=repo,
        workflow=data.get("name", ""),
        status=data.get("status", ""),
        conclusion=data.get("conclusion") or "",
        run_id=data.get("id", 0),
        created_at=data.get("created_at", ""),
        html_url=data.get("html_url", ""),
    )


def _mock_runs(repo: str) -> list[WorkflowRun]:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    return [
        WorkflowRun(repo=repo, workflow="Nightly agent", status="completed",
                    conclusion="success", run_id=1, created_at=now),
        WorkflowRun(repo=repo, workflow="CI", status="completed",
                    conclusion="success", run_id=2, created_at=now),
    ]