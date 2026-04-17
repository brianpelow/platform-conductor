"""Tests for conductor data models."""

from conductor.core.models import WorkflowRun, RepoHealth, PlatformHealth


def test_workflow_run_succeeded() -> None:
    run = WorkflowRun(repo="test", workflow="CI", status="completed", conclusion="success")
    assert run.succeeded is True
    assert run.failed is False


def test_workflow_run_failed() -> None:
    run = WorkflowRun(repo="test", workflow="CI", status="completed", conclusion="failure")
    assert run.failed is True
    assert run.succeeded is False


def test_workflow_run_is_agent() -> None:
    run = WorkflowRun(repo="test", workflow="Nightly agent", status="completed", conclusion="success")
    assert run.is_agent is True


def test_workflow_run_is_not_agent() -> None:
    run = WorkflowRun(repo="test", workflow="CI", status="completed", conclusion="success")
    assert run.is_agent is False


def test_repo_health_defaults() -> None:
    health = RepoHealth(repo="test-repo")
    assert health.health_score == 0
    assert health.status == "unknown"
    assert health.agent_succeeded is False


def test_platform_health_pct() -> None:
    platform = PlatformHealth(total_repos=15, healthy_repos=12)
    assert platform.health_pct == 80.0


def test_platform_health_pct_zero() -> None:
    platform = PlatformHealth(total_repos=0, healthy_repos=0)
    assert platform.health_pct == 0.0