# Install for VS Code

## Give this to a coding agent

Replace `<PDF_PATH>` with the local path to a text-layer PDF, then paste this prompt into a VS Code coding agent:

> Install Local Spec Search from https://github.com/Iris-cys/local-spec-search in an isolated Python environment. Follow INSTALL.md. Index `<PDF_PATH>` for this workspace, run `spec-search doctor`, and show me the result. Do not upload the PDF or index anywhere.

The agent should perform the following equivalent steps.

## Windows PowerShell

```powershell
py -m venv .spec-search-runtime
.\.spec-search-runtime\Scripts\python.exe -m pip install --upgrade pip
.\.spec-search-runtime\Scripts\python.exe -m pip install "git+https://github.com/Iris-cys/local-spec-search.git"
.\.spec-search-runtime\Scripts\spec-search.exe init "C:\path\to\spec.pdf" --workspace .
.\.spec-search-runtime\Scripts\spec-search.exe doctor --workspace .
```

## macOS or Linux

```bash
python3 -m venv .spec-search-runtime
.spec-search-runtime/bin/python -m pip install --upgrade pip
.spec-search-runtime/bin/python -m pip install "git+https://github.com/Iris-cys/local-spec-search.git"
.spec-search-runtime/bin/spec-search init "/path/to/spec.pdf" --workspace .
.spec-search-runtime/bin/spec-search doctor --workspace .
```

`init` builds `.spec-search/index.sqlite` and merges a `local-spec-search` server into `.vscode/mcp.json`. Existing MCP servers are preserved. If that file is invalid JSON, installation stops rather than overwriting it.

Reload VS Code. On first start, review and trust the local MCP server. The tools `search_evidence` and `read_pages` then appear in agent chat.

## Upgrade

Run the same `pip install --upgrade "git+..."` command with the runtime Python, then rerun `init`. Index compatibility is checked by version.

## Uninstall

Delete the `local-spec-search` entry from `.vscode/mcp.json`, then remove `.spec-search-runtime` and `.spec-search` from the workspace. Your source PDF is never deleted.
