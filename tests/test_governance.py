"""Tests for governance scorecard."""

import tempfile
from pathlib import Path
from conductor.governance.scorecard import (
    score_repo_governance, compute_platform_governance,
    RepoGovernanceScore, PlatformGovernanceReport
)


def make_compliant_repo(tmpdir: str) -> Path:
    path = Path(tmpdir)
    (path / ".github").mkdir()
    (path / ".github" / "CODEOWNERS").write_text("* @brianpelow")
    (path / ".github" / "workflows").mkdir()
    (path / ".github" / "workflows" / "ci.yml").write_text("name: CI\non:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n")
    (path / ".github" / "workflows" / "nightly-agent.yml").write_text("name: Nightly\non:\n  schedule:\n    - cron: '0 2 * * *'\njobs:\n  agent:\n    runs-on: ubuntu-latest\n")
    (path / "docs" / "adr").mkdir(parents=True)
    (path / "CHANGELOG.md").write_text(f"# Changelog\n\n## [0.1.0] - {__import__('datetime').date.today().isoformat()}\n\n### Added\n- Initial release")
    (path / "CONTRIBUTING.md").write_text("# Contributing")
    (path / "LICENSE").write_text("Apache 2.0")
    (path / "tests").mkdir()
    (path / "tests" / "test_main.py").write_text("def test_x(): pass")
    return path


def test_fully_compliant_repo() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = make_compliant_repo(tmpdir)
        score = score_repo_governance(path, "test-repo")
        assert score.total == 100
        assert score.level == "fully-compliant"
        assert len(score.checks_failed) == 0


def test_empty_repo_scores_zero() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        score = score_repo_governance(Path(tmpdir), "empty-repo")
        assert score.total == 0
        assert score.level == "non-compliant"


def test_partial_compliance() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        (path / "LICENSE").write_text("Apache 2.0")
        (path / "CONTRIBUTING.md").write_text("# Contributing")
        (path / "CHANGELOG.md").write_text(f"# Changelog\n\n## [0.1.0] - {__import__('datetime').date.today().isoformat()}")
        score = score_repo_governance(path, "partial-repo")
        assert 0 < score.total < 100
        assert score.level in ("non-compliant", "mostly-compliant")


def test_platform_governance_report() -> None:
    with tempfile.TemporaryDirectory() as t1:
        with tempfile.TemporaryDirectory() as t2:
            p1 = make_compliant_repo(t1)
            p2 = Path(t2)
            report = compute_platform_governance([("repo-a", p1), ("repo-b", p2)])
            assert report.repo_count == 2
            assert report.avg_score > 0
            assert report.governance_level in (1, 2, 3, 4, 5)
            assert report.fully_compliant == 1


def test_governance_level_elite() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = make_compliant_repo(tmpdir)
        report = compute_platform_governance([("repo", path)] * 5)
        assert report.governance_level >= 4


def test_top_gaps_identified() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        score = score_repo_governance(Path(tmpdir), "empty")
        assert len(score.checks_failed) > 0