# AI Autonomous Code Auditor

Local-first CLI and dashboard for AST-aware repository scanning, hybrid retrieval, OWASP-oriented rules, and optional free-tier LLM recommendations.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e ".[dev,treesitter]"
copy .env.example .env
audit scan --path C:\path\to\repository --format markdown
audit dashboard
```

Set at least one provider key in `.env` for LLM enrichment. Without one, deterministic static findings and reports still work. Docker users can set `AUDIT_TARGET_PATH` then run `docker compose up --build`.

## Commands

`audit scan --path <repo> --format json|markdown|github|pr-comment` scans a local path or public GitHub URL. Use `--fail-on critical|high|medium|low` to return exit code 1 at a chosen severity threshold. Supplying file paths without `--path` performs a fast explicit-file scan for pre-commit.

`audit fix --issue-id <id>` generates a draft unified diff; `audit test --issue-id <id>` generates a regression test. Neither modifies source files.

## Security model

Repository files are processed locally. Code is sent to an LLM only when an API key is configured. Generated patches are drafts: review and apply them manually.

## CI/CD integration

```yaml
name: Code audit
on: [pull_request]
permissions:
  contents: read
  pull-requests: write
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Anurag058-jp/AI-Autonomous-code-auditor@main
        with:
          path: .
          format: pr-comment
          fail-on: high
          groq-api-key: ${{ secrets.GROQ_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

The root `action.yml` emits GitHub workflow annotations when `format: github`. With `format: pr-comment`, it creates or updates one marked PR comment with a severity summary and expandable findings.

## Pre-commit

The root `.pre-commit-hooks.yaml` publishes the built-in hook. Reference this repository in a consuming project's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Anurag058-jp/AI-Autonomous-code-auditor
    rev: v0.1.0
    hooks:
      - id: zero-cost-code-auditor
```

Install the optional development tools if needed with `pip install -e ".[dev,treesitter]"`, then run `pre-commit install` and `pre-commit run --all-files`.

## Windows installer

The repository includes a reproducible Windows distribution build. It bundles the Python runtime dependencies into a desktop dashboard executable and CLI executable; no Python installation is required for end users. See [`packaging/README.md`](packaging/README.md) to build the bundles and compile the Inno Setup installer. API keys are never packaged: users configure their own optional keys in `%LOCALAPPDATA%\ZeroCostAICodeAuditor\.env`.
