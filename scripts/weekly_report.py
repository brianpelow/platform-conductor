"""Weekly report — generates and posts platform health summary."""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent


def run_weekly_report() -> None:
    from conductor.core.config import ConductorConfig
    from conductor.monitors.github import GitHubMonitor
    from conductor.reporters.weekly import compute_platform_health, generate_weekly_narrative, format_discussion_post
    from conductor.reporters.discussions import post_to_discussions

    config = ConductorConfig.from_env()
    monitor = GitHubMonitor(config)
    repo_health = monitor.check_all_repos()
    platform = compute_platform_health(repo_health, config)
    narrative = generate_weekly_narrative(platform, config)
    platform.weekly_narrative = narrative

    today = date.today().isoformat()
    body = format_discussion_post(platform, narrative)

    out = REPO_ROOT / "docs" / "reports" / f"weekly-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body)
    print(f"[conductor] Weekly report saved -> {out}")

    title = f"Weekly Platform Health — {today} (score: {platform.platform_score}/100)"
    posted = post_to_discussions(title, body, config)
    if posted:
        print("[conductor] Posted to GitHub Discussions")
    else:
        print("[conductor] Discussions post skipped (no token or mock mode)")


if __name__ == "__main__":
    print(f"[conductor] Starting weekly report - {date.today().isoformat()}")
    run_weekly_report()
    print("[conductor] Done.")