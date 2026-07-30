from collections import Counter
from ..models import Finding, Severity


SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


def _escape(value: str, property_value: bool = False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return value.replace(":", "%3A").replace(",", "%2C") if property_value else value


def github_annotations(findings: list[Finding]) -> str:
    """Render findings as GitHub Actions workflow commands."""
    lines = []
    for finding in findings:
        level = "error" if finding.severity in {Severity.CRITICAL, Severity.HIGH} else "warning"
        properties = f"file={_escape(finding.file_path, True)},line={finding.start_line},title={_escape(finding.title, True)}"
        lines.append(f"::{level} {properties}::{_escape(finding.description)}")
    return "\n".join(lines)


def pr_comment_report(findings: list[Finding], files_scanned: int, drafts: dict[str, str] | None = None) -> str:
    """Create a compact, idempotent-friendly Markdown body for pull-request comments."""
    counts = Counter(finding.severity.value for finding in findings)
    lines = [
        "<!-- zero-cost-code-auditor -->",
        "## Zero-Cost AI Code Auditor",
        "",
        "| Files scanned | Total | Critical | High | Medium | Low |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {files_scanned} | {len(findings)} | {counts['critical']} | {counts['high']} | {counts['medium']} | {counts['low']} |",
    ]
    if not findings:
        return "\n".join(lines + ["", "No findings detected.", ""])
    lines += ["", "### Findings"]
    for finding in findings:
        lines += [
            "",
            f"<details><summary><strong>{finding.severity.value.upper()}</strong> {finding.title} — <code>{finding.file_path}:{finding.start_line}</code></summary>",
            "",
            finding.description,
            "",
            "```text",
            finding.evidence,
            "```",
            "",
            f"**Suggested fix:** {finding.remediation}",
        ]
        if drafts and finding.id in drafts:
            lines += ["", "**LLM draft (review before applying):**", "", "```diff", drafts[finding.id], "```"]
        lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


def meets_threshold(findings: list[Finding], threshold: Severity | None) -> bool:
    return threshold is not None and any(SEVERITY_ORDER[finding.severity] <= SEVERITY_ORDER[threshold] for finding in findings)
