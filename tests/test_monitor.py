"""Tests for GitHub monitor."""

from conductor.core.config import ConductorConfig
from conductor.monitors.github import GitHubMonitor, _mock_runs


def test_mock_runs_returns_two_runs() -> None:
    runs = _mock_runs("test-repo")
    assert len(runs) == 2
    assert all(r.repo == "test-repo" for r in runs)


def test_mock_runs_all_succeed() -> None:
    runs = _mock_runs("test-repo")
    assert all(r.succeeded for r in runs)


def test_get_recent_runs_no_token_returns_mock() -> None:
    config = ConductorConfig()
    monitor = GitHubMonitor(config)
    runs = monitor.get_recent_runs("repoforge")
    assert len(runs) > 0


def test_get_repo_health_no_token() -> None:
    config = ConductorConfig()
    monitor = GitHubMonitor(config)
    health = monitor.get_repo_health("repoforge")
    assert health.repo == "repoforge"
    assert health.health_score >= 0
    assert health.status in ("healthy", "degraded", "failed", "unknown")


def test_check_all_repos_returns_15() -> None:
    config = ConductorConfig()
    monitor = GitHubMonitor(config)
    results = monitor.check_all_repos()
    assert len(results) == 15