import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import pathspec

EXCLUDED_DIRS = {".git", "node_modules", "venv", ".venv", "dist", "build", "coverage", "__pycache__"}
CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php", ".cs", ".c", ".h", ".cpp", ".rs"}


def resolve_repository(source: str) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    path = Path(source).expanduser()
    if path.exists():
        return path.resolve(), None
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"} and parsed.netloc == "github.com":
        temp = tempfile.TemporaryDirectory(prefix="audit-repo-")
        result = subprocess.run(["git", "clone", "--depth", "1", source, temp.name], capture_output=True, text=True)
        if result.returncode:
            temp.cleanup()
            raise ValueError(f"GitHub clone failed: {result.stderr.strip()}")
        return Path(temp.name), temp
    raise ValueError("Path must exist or be a public https://github.com/... repository URL")


def scan_files(root: Path) -> list[Path]:
    ignore_file = root / ".gitignore"
    spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_file.read_text(errors="ignore").splitlines()) if ignore_file.exists() else pathspec.PathSpec([])
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        relative = path.relative_to(root)
        if spec.match_file(relative.as_posix()) or path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        try:
            if b"\0" not in path.read_bytes()[:4096]:
                files.append(path)
        except OSError:
            continue
    return files


def scan_explicit_files(paths: list[Path], root: Path) -> list[Path]:
    """Filter a pre-commit-provided file list without walking the repository."""
    ignore_file = root / ".gitignore"
    spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_file.read_text(errors="ignore").splitlines()) if ignore_file.exists() else pathspec.PathSpec([])
    selected: list[Path] = []
    for candidate in paths:
        path = candidate.resolve()
        if not path.is_file() or path.suffix.lower() not in CODE_EXTENSIONS or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        try:
            relative = path.relative_to(root)
            if spec.match_file(relative.as_posix()) or b"\0" in path.read_bytes()[:4096]:
                continue
        except (OSError, ValueError):
            continue
        selected.append(path)
    return selected
