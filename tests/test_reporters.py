"""Tests for weekly reporter."""

from conductor.core.config import ConductorConfig
from conductor.core.models import RepoHealth
from conductor.reporters.weekly import compute_platform_health, generate_weekly_narrative, format_discussion_post


def make_repo_health(repo: str, score: int = 90, status: str = "healthy") -> RepoHealth:
    return RepoHealth(
        repo=repo, health_score=score, status=status,
        agent_succeeded=score >= 80, ci_succeeded=True,
    )


def test_compute_platform_health() -> None:
    config = ConductorConfig()
    repo_health = [make_repo_health(f"repo-{i}") for i in range(15)]
    platform = compute_platform_health(repo_health, config)
    assert platform.total_repos == 15
    assert platform.healthy_repos == 15
    assert platform.platform_score > 0


def test_compute_platform_health_with_failures() -> None:
    config = ConductorConfig()
    repo_health = [make_repo_health(f"repo-{i}") for i in range(12)]
    repo_health += [make_repo_health(f"failed-{i}", score=40, status="failed") for i in range(3)]
    platform = compute_platform_health(repo_health, config)
    assert platform.failed_repos == 3
    assert len(platform.failures) == 3


def test_generate_narrative_no_key() -> None:
    config = ConductorConfig()
    repo_health = [make_repo_health(f"repo-{i}") for i in range(15)]
    platform = compute_platform_health(repo_health, config)
    narrative = generate_weekly_narrative(platform, config)
    assert len(narrative) > 50


def test_format_discussion_post_contains_sections() -> None:
    config = ConductorConfig()
    repo_health = [make_repo_health(f"repo-{i}") for i in range(5)]
    platform = compute_platform_health(repo_health, config)
    body = format_discussion_post(platform, "Test narrative.")
    assert "Weekly Platform Health" in body
    assert "Repo health matrix" in body
    assert "platform-conductor" in body