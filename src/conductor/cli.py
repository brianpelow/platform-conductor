"""platform-conductor CLI entry point."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from conductor.core.config import ConductorConfig
from conductor.monitors.github import GitHubMonitor
from conductor.agents.failure_detector import detect_failures, open_failure_issue
from conductor.reporters.weekly import compute_platform_health, generate_weekly_narrative, format_discussion_post
from conductor.reporters.discussions import post_to_discussions

app = typer.Typer(name="conductor", help="Platform meta-orchestrator for brianpelow portfolio.")
console = Console()


@app.command("status")
def status(
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show current health of all 15 portfolio repos."""
    config = ConductorConfig.from_env()
    monitor = GitHubMonitor(config)

    console.print("[dim]Checking all repos...[/dim]")
    repo_health = monitor.check_all_repos()
    platform = compute_platform_health(repo_health, config)

    if output_json:
        print(json.dumps(platform.model_dump(), indent=2))
        return

    score_color = "green" if platform.platform_score >= 80 else "yellow" if platform.platform_score >= 60 else "red"
    console.print(Panel.fit(
        f"Platform score: [{score_color}]{platform.platform_score}/100[/{score_color}]\n"
        f"Healthy: [green]{platform.healthy_repos}[/green] / {platform.total_repos} repos\n"
        f"Failures: [red]{platform.failed_repos}[/red]",
        title="Platform Health",
        border_style="blue",
    ))

    table = Table(border_style="dim")
    table.add_column("Repo", style="cyan")
    table.add_column("Score", justify="center")
    table.add_column("Agent", justify="center")
    table.add_column("CI", justify="center")
    table.add_column("Status")

    for r in sorted(repo_health, key=lambda x: x.health_score, reverse=True):
        color = "green" if r.status == "healthy" else "yellow" if r.status == "degraded" else "red"
        table.add_row(
            r.repo,
            str(r.health_score),
            "[green]✓[/green]" if r.agent_succeeded else "[red]✗[/red]",
            "[green]✓[/green]" if r.ci_succeeded else "[red]✗[/red]",
            f"[{color}]{r.status}[/{color}]",
        )
    console.print(table)


@app.command("report")
def report(
    post: bool = typer.Option(False, "--post", help="Post to GitHub Discussions"),
    output: str = typer.Option("", "--output", "-o", help="Save report to file"),
) -> None:
    """Generate weekly platform health report."""
    config = ConductorConfig.from_env()
    monitor = GitHubMonitor(config)

    repo_health = monitor.check_all_repos()
    platform = compute_platform_health(repo_health, config)
    narrative = generate_weekly_narrative(platform, config)
    platform.weekly_narrative = narrative

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    discussion_body = format_discussion_post(platform, narrative)

    if output:
        Path(output).write_text(discussion_body)
        console.print(f"[green]✓[/green] Report saved to [cyan]{output}[/cyan]")
    else:
        out = Path("docs/reports") / f"weekly-{date}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(discussion_body)
        console.print(f"[green]✓[/green] Report saved to [cyan]{out}[/cyan]")

    if post:
        title = f"Weekly Platform Health — {date} (score: {platform.platform_score}/100)"
        success = post_to_discussions(title, discussion_body, config)
        if success:
            console.print("[green]✓[/green] Posted to GitHub Discussions")
        else:
            console.print("[yellow]⚠[/yellow] Could not post to Discussions (check token permissions)")


@app.command("issues")
def issues() -> None:
    """Detect failures and open GitHub issues."""
    config = ConductorConfig.from_env()
    monitor = GitHubMonitor(config)

    repo_health = monitor.check_all_repos()
    failures = detect_failures(repo_health)

    if not failures:
        console.print("[green]✓[/green] No failures detected across all repos.")
        return

    console.print(f"[yellow]⚠[/yellow] {len(failures)} repo(s) with failures:\n")
    for health in failures:
        opened = open_failure_issue(health.repo, health, config)
        status = "[green]issue opened[/green]" if opened else "[dim]mock/skipped[/dim]"
        console.print(f"  {health.repo} — score {health.health_score}/100 — {status}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()