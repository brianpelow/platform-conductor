"""Nightly health check â€” monitors all 15 portfolio repos."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent


def run_health_check() -> None:
    from conductor.core.config import ConductorConfig
    from conductor.monitors.github import GitHubMonitor
    from conductor.agents.failure_detector import detect_failures, open_failure_issue
    from conductor.reporters.weekly import compute_platform_health

    config = ConductorConfig.from_env()
    monitor = GitHubMonitor(config)
    repo_health = monitor.check_all_repos()
    platform = compute_platform_health(repo_health, config)

    failures = detect_failures(repo_health)
    issues_opened = 0
    for health in failures:
        if open_failure_issue(health.repo, health, config):
            issues_opened += 1

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": date.today().isoformat(),
        "platform_score": platform.platform_score,
        "healthy_repos": platform.healthy_repos,
        "failed_repos": platform.failed_repos,
        "total_repos": platform.total_repos,
        "failures": platform.failures,
        "issues_opened": issues_opened,
        "repos": [
            {"repo": r.repo, "score": r.health_score, "status": r.status,
             "agent_ok": r.agent_succeeded, "ci_ok": r.ci_succeeded}
            for r in repo_health
        ],
    }

    out = REPO_ROOT / "docs" / "health-report.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"[conductor] Health check complete â€” score: {platform.platform_score}/100, failures: {len(platform.failures)}")
    if issues_opened:
        print(f"[conductor] Opened {issues_opened} failure issue(s)")


def refresh_changelog() -> None:
    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        return
    today = date.today().isoformat()
    content = changelog.read_text()
    if today not in content:
        content = content.replace("## [Unreleased]", f"## [Unreleased]\n\n_Last checked: {today}_", 1)
        changelog.write_text(content)


def run_governance() -> None:
    import subprocess, sys
    subprocess.run([sys.executable, str(Path(__file__).parent / 'governance_report.py')])


if __name__ == "__main__":
    print(f"[conductor] Starting nightly health check - {date.today().isoformat()}")
    run_health_check()
    refresh_changelog()
    print("[conductor] Done.")