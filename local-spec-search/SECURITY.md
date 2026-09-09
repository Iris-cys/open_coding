# Security

Local MCP servers execute code on the user's machine. Review the repository and generated `.vscode/mcp.json` before approving the server in VS Code.

This server is read-only after indexing and does not execute text found in documents. Source text is treated as untrusted data. The index contains extracted document text and must receive the same access protection as the source PDF.

Report vulnerabilities privately to the repository owner through GitHub's private vulnerability reporting when enabled. Do not include proprietary documents or extracted text in a public report.
