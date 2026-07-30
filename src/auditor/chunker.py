import ast
import hashlib
import re
from pathlib import Path
from .models import CodeChunk

LANGUAGES = {".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "tsx", ".java": "java", ".go": "go", ".rb": "ruby", ".php": "php", ".cs": "c_sharp", ".c": "c", ".h": "c", ".cpp": "cpp", ".rs": "rust"}
DECLARATION_TYPES = {"function_definition", "function_declaration", "method_definition", "method_declaration", "class_definition", "class_declaration", "interface_declaration", "lexical_declaration"}


def _id(path: str, start: int, name: str) -> str:
    return hashlib.sha1(f"{path}:{start}:{name}".encode()).hexdigest()[:16]


def _python_chunks(file: Path, root: Path, text: str) -> list[CodeChunk]:
    tree = ast.parse(text)
    imports = [n.names[0].name for n in tree.body if isinstance(n, ast.Import)]
    imports += [n.module or "" for n in tree.body if isinstance(n, ast.ImportFrom)]
    lines = text.splitlines()
    output = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start, end = node.lineno, getattr(node, "end_lineno", node.lineno)
            output.append(CodeChunk(_id(str(file), start, node.name), str(file.relative_to(root)), start, end, node.name, type(node).__name__, imports, "\n".join(lines[start - 1:end])))
    return output


def _tree_sitter_chunks(file: Path, root: Path, text: str) -> list[CodeChunk]:
    """Use Tree-sitter when its language pack is installed; caller falls back safely."""
    from tree_sitter_language_pack import get_parser
    parser = get_parser(LANGUAGES[file.suffix.lower()])
    tree = parser.parse(text.encode())
    output: list[CodeChunk] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in DECLARATION_TYPES:
            start, end = node.start_point.row + 1, node.end_point.row + 1
            snippet = "\n".join(text.splitlines()[start - 1:end])
            name_match = re.search(r"(?:function|class|interface|def|func)\s+([\w$]+)", snippet)
            name = name_match.group(1) if name_match else node.type
            output.append(CodeChunk(_id(str(file), start, name), str(file.relative_to(root)), start, end, name, node.type, [], snippet))
            continue
        stack.extend(reversed(node.named_children))
    return output


def chunk_file(file: Path, root: Path) -> list[CodeChunk]:
    text = file.read_text(encoding="utf-8", errors="replace")
    if file.suffix == ".py":
        try:
            chunks = _python_chunks(file, root, text)
            if chunks:
                return chunks
        except SyntaxError:
            pass
    try:
        chunks = _tree_sitter_chunks(file, root, text)
        if chunks:
            return chunks
    except Exception:
        # Tree-sitter language packs can be unavailable or have a locked cache on
        # developer machines. Parsing is an enhancement; semantic fallback keeps
        # the audit usable in that case.
        pass
    lines, output = text.splitlines(), []
    pattern = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class|interface|def|func)\s+([\w$]+)", re.M)
    matches = list(pattern.finditer(text))
    for index, match in enumerate(matches):
        start = text[:match.start()].count("\n") + 1
        end = text[:matches[index + 1].start()].count("\n") if index + 1 < len(matches) else len(lines)
        name = match.group(1)
        output.append(CodeChunk(_id(str(file), start, name), str(file.relative_to(root)), start, end, name, "semantic_block", [], "\n".join(lines[start - 1:end])))
    return output or [CodeChunk(_id(str(file), 1, "module"), str(file.relative_to(root)), 1, len(lines), "module", "module", [], text)]
