from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CodeChunk:
    id: str
    file_path: str
    start_line: int
    end_line: int
    name: str
    kind: str
    imports: list[str]
    content: str


@dataclass
class Finding:
    id: str
    rule_id: str
    severity: Severity
    title: str
    description: str
    file_path: str
    start_line: int
    end_line: int
    evidence: str
    remediation: str
    confidence: float = 0.8
    source: str = "static"
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data

