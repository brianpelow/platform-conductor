"""Governance report script — sweeps all portfolio repos and produces scored report."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

REPO_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = REPO_ROOT.parent

PORTFOLIO_REPOS = [
    "repoforge", "pr-autopilot", "runbook-gen",
    "mcp-incident-intel", "mcp-compliance-grc", "mcp-developer-portal",
    "TeamHealthRadar", "PlatformSLOBoard", "TechDebtLedger",
    "IncidentPilot", "DataPipelineAgent", "BoardroomBrief",
    "innersource-scorecard", "service-catalog-sync", "platform-maturity-model",
    "orbit-platform", "cab-automation", "fintech-platform-reference",
    "vibe-check-cli", "code-roast", "sports-analytics-for-engineers",
    "platform-conductor",
]


def run_governance_report() -> None:
    from conductor.governance.scorecard import compute_platform_governance

    repo_paths = [
        (repo, PROJECTS_DIR / repo)
        for repo in PORTFOLIO_REPOS
    ]

    report = compute_platform_governance(repo_paths)

    out = REPO_ROOT / "docs" / "governance-report.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "generated_at": report.generated_at,
        "date": date.today().isoformat(),
        "avg_score": report.avg_score,
        "governance_level": report.governance_level,
        "governance_level_name": report.governance_level_name,
        "repo_count": report.repo_count,
        "fully_compliant": report.fully_compliant,
        "mostly_compliant": report.mostly_compliant,
        "non_compliant": report.non_compliant,
        "top_gaps": report.top_gaps,
        "repos": [
            {
                "repo": r.repo,
                "score": r.total,
                "level": r.level,
                "passed": len(r.checks_passed),
                "failed": r.checks_failed,
            }
            for r in sorted(report.repo_scores, key=lambda x: -x.total)
        ],
    }, indent=2))

    print(f"[governance] Platform governance: Level {report.governance_level}/5 ({report.governance_level_name})")
    print(f"[governance] Average score: {report.avg_score}/100")
    print(f"[governance] Fully compliant: {report.fully_compliant}/{report.repo_count} repos")
    if report.top_gaps:
        print(f"[governance] Top gaps: {', '.join(report.top_gaps[:3])}")
    print(f"[governance] Report saved -> {out}")


if __name__ == "__main__":
    print(f"[governance] Starting governance report - {date.today().isoformat()}")
    run_governance_report()
    print("[governance] Done.")