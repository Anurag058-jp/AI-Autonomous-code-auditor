import json
from pathlib import Path
import typer
from .config import settings
from .report import markdown_report
from .models import Finding, Severity
from .service import AuditService
from .integrations.github import github_annotations, meets_threshold, pr_comment_report

app = typer.Typer(help="Local-first autonomous security code auditor.")


@app.command()
def scan(
    files: list[Path] = typer.Argument(None, help="Explicit files to scan (used by pre-commit)."),
    path: str | None = typer.Option(None, "--path", help="Repository path or public GitHub URL."),
    format: str = typer.Option("markdown", "--format"),
    fail_on: Severity | None = typer.Option(None, "--fail-on", help="Exit 1 for findings at or above this severity."),
):
    """Scan a local repository or a public GitHub URL."""
    if path is None and not files:
        raise typer.BadParameter("Provide --path <repository> or one or more files.")
    source = path or str(Path.cwd())
    result = AuditService().scan(source, explicit_files=files or None)
    findings = [Finding(**{**finding, "severity": Severity(finding["severity"])}) for finding in result["findings"]]
    if format == "json":
        typer.echo(json.dumps(result, indent=2))
    elif format == "markdown":
        typer.echo(markdown_report(result["repository"], findings, result["files_scanned"]))
    elif format == "github":
        typer.echo(github_annotations(findings))
    elif format == "pr-comment":
        drafts: dict[str, str] = {}
        # Diffs are generated only for this explicitly requested PR format and only when an LLM is configured.
        for finding in findings[:10]:
            try:
                from .llm import LLMClient
                if LLMClient().enabled():
                    drafts[finding.id] = AuditService().generate(result["scan_id"], finding.id, "fix")
            except RuntimeError:
                break
        typer.echo(pr_comment_report(findings, result["files_scanned"], drafts))
    else:
        raise typer.BadParameter("format must be json, markdown, github, or pr-comment")
    if format in {"json", "markdown"}:
        typer.echo(f"Saved report: {settings.data_dir / (result['scan_id'] + '.md')}")
    if meets_threshold(findings, fail_on):
        raise typer.Exit(1)


@app.command()
def fix(scan_id: str = typer.Option(...), issue_id: str = typer.Option(...)):
    """Generate a review-only unified-diff draft for an issue."""
    typer.echo(AuditService().generate(scan_id, issue_id, "fix"))


@app.command()
def test(scan_id: str = typer.Option(...), issue_id: str = typer.Option(...)):
    """Generate a review-only pytest regression-test draft for an issue."""
    typer.echo(AuditService().generate(scan_id, issue_id, "test"))


@app.command()
def serve():
    """Start the FastAPI server."""
    from .api import run
    run()


@app.command()
def dashboard():
    """Start the Streamlit dashboard."""
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("dashboard.py"))], check=True)
