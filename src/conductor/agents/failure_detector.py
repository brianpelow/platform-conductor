"""Failure detector â€” opens GitHub issues when agent runs fail."""

from __future__ import annotations

import httpx
from conductor.core.models import RepoHealth
from conductor.core.config import ConductorConfig


def detect_failures(repo_health: list[RepoHealth]) -> list[RepoHealth]:
    """Return repos with failed or degraded agent runs."""
    return [r for r in repo_health if r.status in ("failed", "degraded") or not r.agent_succeeded]


def open_failure_issue(repo: str, health: RepoHealth, config: ConductorConfig) -> bool:
    """Open a GitHub issue for a failed nightly agent run."""
    if not config.has_github:
        print(f"[mock] Would open issue on {repo}: agent run failed")
        return True
    try:
        title = f"[platform-conductor] Nightly agent failure detected â€” {repo}"
        body = f"""## Nightly agent failure

The platform-conductor detected that the nightly agent workflow failed or did not run in the last 26 hours.

**Repository**: `{config.org}/{repo}`
**Health score**: {health.health_score}/100
**Status**: {health.status}
**Last agent run**: {health.last_agent_run or "unknown"}
**CI passing**: {health.ci_succeeded}

### Recommended actions

1. Check the [Actions tab](https://github.com/{config.org}/{repo}/actions) for error details
2. Verify the nightly-agent.yml workflow is correctly configured
3. Check if required secrets (ANTHROPIC_API_KEY) are set
4. Re-run the workflow manually if needed

---
*Opened automatically by [platform-conductor](https://github.com/{config.org}/platform-conductor)*
"""
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"https://api.github.com/repos/{config.org}/{repo}/issues",
                headers={
                    "Authorization": f"Bearer {config.github_token}",
                    "Accept": "application/vnd.github+json",
                },
                json={"title": title, "body": body, "labels": ["agent-failure", "automated"]},
            )
            return response.status_code == 201
    except Exception:
        return False