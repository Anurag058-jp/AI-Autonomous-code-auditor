import hashlib
import re
from dataclasses import dataclass
from .models import Finding, Severity


@dataclass(frozen=True)
class Rule:
    id: str
    severity: Severity
    title: str
    pattern: str
    description: str
    remediation: str


RULES = [
    Rule("SEC001", Severity.HIGH, "Possible hardcoded secret", r"(?i)(api[_-]?key|secret|password|token)\s*[=:]\s*['\"][^'\"]{8,}", "A credential appears in source code.", "Move it to an environment variable or secret manager and rotate the exposed value."),
    Rule("SEC002", Severity.HIGH, "Possible SQL injection", r"(?i)(execute|query)\s*\(\s*(?:f['\"]|['\"].*?(?:\+|%))", "SQL appears to be constructed from interpolated input.", "Use parameterized queries and validate untrusted input."),
    Rule("SEC003", Severity.HIGH, "Unsafe deserialization", r"(?i)(pickle\.loads|yaml\.load\s*\([^,)]*\))", "Unsafe deserialization can execute attacker-controlled code.", "Use safe loaders or a non-executable serialization format."),
    Rule("SEC004", Severity.MEDIUM, "Debug mode enabled", r"(?i)debug\s*=\s*true", "Debug mode may expose internal details in production.", "Disable debug mode outside development."),
    Rule("PERF001", Severity.MEDIUM, "Possible quadratic loop", r"(?s)for .+?:.*?for .+?:", "Nested loops can grow quadratically with input size.", "Verify bounds; use indexing, batching, or a more suitable data structure."),
    Rule("QUAL001", Severity.LOW, "Broad exception handler", r"except\s*(?:Exception)?\s*:", "A broad exception can hide failures and make recovery unreliable.", "Catch expected exception types and log or re-raise unexpected failures."),
]


def run_rules(file_path: str, content: str) -> list[Finding]:
    findings = []
    for rule in RULES:
        for match in re.finditer(rule.pattern, content):
            line = content[:match.start()].count("\n") + 1
            digest = hashlib.sha1(f"{rule.id}:{file_path}:{line}".encode()).hexdigest()[:10]
            findings.append(Finding(f"{rule.id}-{digest}", rule.id, rule.severity, rule.title, rule.description, file_path, line, line, match.group(0)[:300], rule.remediation, references=["OWASP Top 10"]))
    return findings

