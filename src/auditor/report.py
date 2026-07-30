from collections import Counter
from .models import Finding


def markdown_report(repo: str, findings: list[Finding], files_scanned: int) -> str:
    counts = Counter(f.severity.value for f in findings)
    lines = ["# Audit Report", "", f"**Repository:** `{repo}`  ", f"**Files scanned:** {files_scanned}  ", f"**Findings:** {len(findings)} (critical: {counts['critical']}, high: {counts['high']}, medium: {counts['medium']}, low: {counts['low']})", "", "## Findings"]
    for finding in findings:
        lines += ["", f"### [{finding.severity.value.upper()}] {finding.title}", f"- ID: `{finding.id}`", f"- Location: `{finding.file_path}:{finding.start_line}`", f"- Evidence: `{finding.evidence}`", f"- Why it matters: {finding.description}", f"- Recommended fix: {finding.remediation}"]
    return "\n".join(lines) + "\n"

