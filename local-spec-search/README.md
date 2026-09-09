# Local Spec Search

Offline, evidence-first search for a long technical PDF, exposed to VS Code agents through MCP. It returns the source file, PDF page number, bookmark section, exact excerpt, and neighboring page text; the AI remains responsible for reading the evidence and writing the answer.

No Docker, separately managed background service, API key, or cloud vector database is required. VS Code starts the local MCP process as needed. Indexing and retrieval stay on the local machine.

## Install with one request

Give a VS Code coding agent the repository URL, the PDF path, and this instruction:

> Install Local Spec Search from this GitHub repository, follow INSTALL.md, index my PDF for this workspace, and run the doctor check. Keep the PDF and index local.

Exact agent-ready prompt and manual Windows/macOS/Linux commands are in [INSTALL.md](INSTALL.md).

## What gets installed

MCP is the connection layer between the editor's AI and this local search engine. The retrieval core is the PDF parser plus SQLite FTS5, TF-IDF, phrase matching, and bookmark-aware ranking. MCP itself is not the search algorithm.

## Direct use

```bash
spec-search init "/path/to/spec.pdf" --workspace .
spec-search doctor --workspace .
spec-search search "How does Function Level Reset work?" --workspace . --full
```

After `init`, reload VS Code, approve the local server when prompted, and ask the agent:

> Search the indexed specification for Function Level Reset. Cite the PDF page and section, quote only the minimum evidence needed, and use read_pages to check nearby conditions or exceptions.

The MCP server exposes two read-only tools:

- `search_evidence`: returns up to five ranked evidence groups with page and section metadata.
- `read_pages`: returns exact indexed text for up to five consecutive pages.

## Privacy boundary

The program itself makes no network calls and does not generate answers. However, VS Code can send MCP tool results to the model configured in the editor. Use a local model/client when document text is not allowed to leave the machine. Do not commit `.spec-search/`, source PDFs, or generated indexes.

## Supported scope

Version 2.2 supports one text-layer PDF per workspace and is tuned/tested on the PCI Express 7.0 specification. It does not yet support scanned-PDF OCR, images, complex table semantics, DOCX/PPTX/XLSX, a multi-document corpus, or general multilingual embeddings. Chinese PCIe queries use a bounded domain alias map. Candidate retrieval is not proof that a proposition is true; the server can abstain when vocabulary coverage is weak.

These limits are deliberate release boundaries, not hidden roadmap claims. Measured PCIe results and failures are in [docs/VALIDATION.md](docs/VALIDATION.md).

## Development

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -p "test_*.py"
ruff check src tests
python -m build
twine check dist/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the acceptance bar. The project is MIT licensed.
