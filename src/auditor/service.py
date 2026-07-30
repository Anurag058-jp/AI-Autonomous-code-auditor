import json
from dataclasses import asdict
from pathlib import Path
from .chunker import chunk_file
from .config import settings
from .indexing import LocalVectorStore
from .llm import LLMClient
from .models import Finding, Severity
from .report import markdown_report
from .rules import run_rules
from .scanner import resolve_repository, scan_explicit_files, scan_files


class AuditService:
    def scan(self, source: str, explicit_files: list[Path] | None = None) -> dict:
        root, temp = resolve_repository(source)
        try:
            files = scan_explicit_files(explicit_files, root) if explicit_files is not None else scan_files(root)
            chunks, findings = [], []
            for file in files:
                text = file.read_text(encoding="utf-8", errors="replace")
                relative = str(file.relative_to(root))
                findings.extend(run_rules(relative, text))
                chunks.extend(chunk_file(file, root))
            llm = LLMClient()
            if llm.enabled() and chunks:
                try:
                    for item in llm.analyze([asdict(chunk) for chunk in chunks[:20]]):
                        severity = Severity(item.get("severity", "medium"))
                        evidence = str(item.get("evidence", ""))[:500]
                        digest = __import__("hashlib").sha1(f"LLM:{item.get('file_path')}:{item.get('start_line')}:{item.get('title')}".encode()).hexdigest()[:10]
                        findings.append(Finding(f"LLM-{digest}", "LLM001", severity, str(item.get("title", "LLM review finding")), str(item.get("description", "")), str(item.get("file_path", "unknown")), int(item.get("start_line", 1)), int(item.get("end_line", item.get("start_line", 1))), evidence, str(item.get("remediation", "Review and remediate this finding.")), float(item.get("confidence", 0.6)), "llm", ["OWASP Top 10"]))
                except (RuntimeError, ValueError):
                    # A failed optional enrichment must never prevent a local static report.
                    pass
            indexed = LocalVectorStore(str(settings.data_dir / "chromadb"), f"scan_{__import__('hashlib').sha1(str(root).encode()).hexdigest()[:12]}").persist(chunks)
            result = {"repository": str(root), "files_scanned": len(files), "chunks": [asdict(c) for c in chunks], "findings": [f.to_dict() for f in findings], "vector_indexed": indexed}
            scan_id = __import__("hashlib").sha1(f"{root}:{len(files)}".encode()).hexdigest()[:12]
            result["scan_id"] = scan_id
            output = settings.data_dir / f"{scan_id}.json"
            output.write_text(json.dumps(result, indent=2), encoding="utf-8")
            (settings.data_dir / f"{scan_id}.md").write_text(markdown_report(str(root), findings, len(files)), encoding="utf-8")
            return result
        finally:
            if temp:
                temp.cleanup()

    def get_scan(self, scan_id: str) -> dict:
        path = settings.data_dir / f"{scan_id}.json"
        if not path.exists():
            raise ValueError(f"Unknown scan: {scan_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def generate(self, scan_id: str, issue_id: str, kind: str) -> str:
        result = self.get_scan(scan_id)
        finding = next((f for f in result["findings"] if f["id"] == issue_id), None)
        if not finding:
            raise ValueError(f"Unknown issue: {issue_id}")
        if not LLMClient().enabled():
            raise RuntimeError("No selected LLM provider key configured. Add it to .env before generating drafts.")
        target = "a unified diff patch only" if kind == "fix" else "a pytest regression test only"
        return LLMClient().draft(f"Generate {target}. Finding: {json.dumps(finding)}. Do not modify files; this is a review draft.")
