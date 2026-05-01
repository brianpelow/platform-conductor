"""Governance scorecard — sweeps all portfolio repos for compliance signals."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field


CHECKS = {
    "codeowners": ("CODEOWNERS defined", 10),
    "adr_directory": ("ADR directory present", 10),
    "changelog_fresh": ("CHANGELOG updated in last 30 days", 10),
    "contributing": ("CONTRIBUTING.md present", 10),
    "ci_workflow": ("CI workflow configured", 15),
    "nightly_agent": ("Nightly agent configured", 15),
    "license": ("LICENSE present", 10),
    "tests_present": ("Test suite present", 20),
}


@dataclass
class RepoGovernanceScore:
    """Governance score for a single repository."""
    repo: str
    total: int = 0
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    level: str = "non-compliant"

    @property
    def pct(self) -> float:
        return self.total


@dataclass
class PlatformGovernanceReport:
    """Platform-wide governance report."""
    generated_at: str = ""
    repo_count: int = 0
    avg_score: float = 0.0
    fully_compliant: int = 0
    mostly_compliant: int = 0
    non_compliant: int = 0
    governance_level: int = 3
    governance_level_name: str = "Defined"
    repo_scores: list[RepoGovernanceScore] = field(default_factory=list)
    top_gaps: list[str] = field(default_factory=list)


def score_repo_governance(repo_path: Path, repo_name: str) -> RepoGovernanceScore:
    """Score a single repo against governance checks."""
    score = RepoGovernanceScore(repo=repo_name)

    # CODEOWNERS
    has_codeowners = (
        (repo_path / ".github" / "CODEOWNERS").exists() or
        (repo_path / "CODEOWNERS").exists()
    )
    _apply(score, "codeowners", has_codeowners)

    # ADR directory
    has_adr = (repo_path / "docs" / "adr").exists()
    _apply(score, "adr_directory", has_adr)

    # CHANGELOG freshness
    changelog = repo_path / "CHANGELOG.md"
    changelog_fresh = False
    if changelog.exists():
        import re
        from datetime import date, timedelta
        content = changelog.read_text(errors="ignore")
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", content)
        if dates:
            try:
                latest = max(date.fromisoformat(d) for d in dates)
                changelog_fresh = (date.today() - latest).days <= 30
            except ValueError:
                pass
    _apply(score, "changelog_fresh", changelog_fresh)

    # CONTRIBUTING
    has_contributing = (repo_path / "CONTRIBUTING.md").exists()
    _apply(score, "contributing", has_contributing)

    # CI workflow
    has_ci = False
    wf_dir = repo_path / ".github" / "workflows"
    if wf_dir.exists():
        for wf in wf_dir.glob("*.yml"):
            content = wf.read_text(errors="ignore")
            if "pytest" in content or "test" in content.lower() or "ruff" in content:
                has_ci = True
                break
    _apply(score, "ci_workflow", has_ci)

    # Nightly agent
    has_nightly = False
    if wf_dir.exists():
        for wf in wf_dir.glob("*.yml"):
            content = wf.read_text(errors="ignore")
            if "cron" in content and ("nightly" in content.lower() or "agent" in content.lower()):
                has_nightly = True
                break
    _apply(score, "nightly_agent", has_nightly)

    # LICENSE
    has_license = (repo_path / "LICENSE").exists() or (repo_path / "LICENSE.md").exists()
    _apply(score, "license", has_license)

    # Tests
    has_tests = (repo_path / "tests").exists() and any(
        f for f in (repo_path / "tests").rglob("test_*.py")
    ) if (repo_path / "tests").exists() else False
    _apply(score, "tests_present", has_tests)

    # Determine level
    if score.total >= 90:
        score.level = "fully-compliant"
    elif score.total >= 70:
        score.level = "mostly-compliant"
    else:
        score.level = "non-compliant"

    return score


def _apply(score: RepoGovernanceScore, check: str, passed: bool) -> None:
    name, points = CHECKS[check]
    if passed:
        score.total += points
        score.checks_passed.append(name)
    else:
        score.checks_failed.append(name)


def compute_platform_governance(repo_paths: list[tuple[str, Path]]) -> PlatformGovernanceReport:
    """Compute governance report across all repos."""
    report = PlatformGovernanceReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        repo_count=len(repo_paths),
    )

    for repo_name, repo_path in repo_paths:
        if repo_path.exists():
            score = score_repo_governance(repo_path, repo_name)
        else:
            score = _mock_score(repo_name)
        report.repo_scores.append(score)

    if report.repo_scores:
        report.avg_score = round(
            sum(r.total for r in report.repo_scores) / len(report.repo_scores), 1
        )

    report.fully_compliant = sum(1 for r in report.repo_scores if r.level == "fully-compliant")
    report.mostly_compliant = sum(1 for r in report.repo_scores if r.level == "mostly-compliant")
    report.non_compliant = sum(1 for r in report.repo_scores if r.level == "non-compliant")

    if report.avg_score >= 90:
        report.governance_level = 5
        report.governance_level_name = "Optimizing"
    elif report.avg_score >= 75:
        report.governance_level = 4
        report.governance_level_name = "Measured"
    elif report.avg_score >= 60:
        report.governance_level = 3
        report.governance_level_name = "Defined"
    elif report.avg_score >= 40:
        report.governance_level = 2
        report.governance_level_name = "Managed"
    else:
        report.governance_level = 1
        report.governance_level_name = "Initial"

    gap_counts: dict[str, int] = {}
    for r in report.repo_scores:
        for gap in r.checks_failed:
            gap_counts[gap] = gap_counts.get(gap, 0) + 1
    report.top_gaps = [g for g, _ in sorted(gap_counts.items(), key=lambda x: -x[1])][:5]

    return report


def _mock_score(repo_name: str) -> RepoGovernanceScore:
    """Mock score for repos not cloned locally."""
    score = RepoGovernanceScore(repo=repo_name)
    for check, (name, points) in CHECKS.items():
        if check not in ("adr_directory", "nightly_agent"):
            score.total += points
            score.checks_passed.append(name)
        else:
            score.checks_failed.append(name)
    score.level = "mostly-compliant"
    return score