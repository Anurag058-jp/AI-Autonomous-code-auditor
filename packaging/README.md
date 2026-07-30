# Windows distribution

The Windows release uses PyInstaller's `onedir` mode. This keeps Streamlit, ChromaDB, Tree-sitter, and all runtime DLLs beside the executable, which is much more reliable than a single-file build for this application.

## Build the executables

From PowerShell in the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,treesitter]"
.\packaging\build-windows.ps1
```

This produces self-contained application folders; distribute the whole folder or use the installer, not the `.exe` file alone:

- `outputs\windows\AI-Code-Auditor\AI-Code-Auditor.exe` — desktop dashboard
- `outputs\windows\audit\audit.exe` — console CLI

## Build the installer

Install Inno Setup 6, then compile `packaging\installer.iss` using the Inno Setup Compiler. It creates `outputs\windows\installer\Zero-Cost-AI-Code-Auditor-Setup-0.1.0.exe`.

## End-user configuration

The installer never contains API keys. After installation, an end user can create:

`%LOCALAPPDATA%\ZeroCostAICodeAuditor\.env`

using the same variables as `.env.example`. Static scanning works without any key; a Groq or Mistral key enables LLM enrichment and draft fixes.
