from typer.testing import CliRunner
from auditor.cli import app
from auditor.integrations.github import github_annotations, meets_threshold, pr_comment_report
from auditor.models import Finding, Severity


def finding(severity: Severity = Severity.HIGH) -> Finding:
    return Finding("SEC001-example", "SEC001", severity, "Example finding", "Unsafe input detected", "src/app.py", 12, 12, "query(user_input)", "Use parameterized queries.")


def scan_result(severity: Severity = Severity.HIGH) -> dict:
    return {"scan_id": "scan123", "repository": "repo", "files_scanned": 1, "chunks": [], "findings": [finding(severity).to_dict()]}


def test_github_annotation_maps_high_to_error():
    assert github_annotations([finding()]) == "::error file=src/app.py,line=12,title=Example finding::Unsafe input detected"


def test_pr_comment_has_summary_and_details():
    output = pr_comment_report([finding()], 2)
    assert "| 2 | 1 | 0 | 1 | 0 | 0 |" in output
    assert "<details>" in output
    assert "Suggested fix" in output


def test_threshold_respects_severity_order():
    assert meets_threshold([finding(Severity.CRITICAL)], Severity.HIGH)
    assert not meets_threshold([finding(Severity.LOW)], Severity.HIGH)


def test_cli_github_format_and_fail_on(monkeypatch):
    monkeypatch.setattr("auditor.cli.AuditService.scan", lambda *_args, **_kwargs: scan_result())
    result = CliRunner().invoke(app, ["scan", "--path", ".", "--format", "github", "--fail-on", "high"])
    assert result.exit_code == 1
    assert "::error file=src/app.py,line=12,title=Example finding::Unsafe input detected" in result.output


def test_cli_explicit_files_are_forwarded(monkeypatch):
    captured = {}
    def fake_scan(_self, source, explicit_files=None):
        captured["source"], captured["files"] = source, explicit_files
        return scan_result(Severity.LOW)
    monkeypatch.setattr("auditor.cli.AuditService.scan", fake_scan)
    result = CliRunner().invoke(app, ["scan", "example.py", "--format", "github", "--fail-on", "high"])
    assert result.exit_code == 0
    assert captured["files"][0].name == "example.py"
