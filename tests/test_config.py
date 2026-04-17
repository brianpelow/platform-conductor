"""Tests for ConductorConfig."""

from conductor.core.config import ConductorConfig, PORTFOLIO_REPOS


def test_portfolio_repos_count() -> None:
    assert len(PORTFOLIO_REPOS) == 15


def test_config_defaults() -> None:
    config = ConductorConfig()
    assert config.org == "brianpelow"
    assert config.industry == "fintech"
    assert len(config.repos) == 15


def test_has_github_false() -> None:
    config = ConductorConfig()
    assert config.has_github is False


def test_has_github_true() -> None:
    config = ConductorConfig(github_token="test-token")
    assert config.has_github is True


def test_has_api_key_false() -> None:
    config = ConductorConfig()
    assert config.has_api_key is False


def test_all_portfolio_repos_present() -> None:
    expected = [
        "repoforge", "pr-autopilot", "runbook-gen",
        "mcp-incident-intel", "mcp-compliance-grc", "mcp-developer-portal",
        "TeamHealthRadar", "PlatformSLOBoard", "TechDebtLedger",
        "IncidentPilot", "DataPipelineAgent", "BoardroomBrief",
        "innersource-scorecard", "service-catalog-sync", "platform-maturity-model",
    ]
    for repo in expected:
        assert repo in PORTFOLIO_REPOS