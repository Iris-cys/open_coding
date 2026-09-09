"""Workspace configuration and VS Code MCP configuration helpers."""

from __future__ import annotations

import json
from pathlib import Path
import sys

SERVER_NAME = 'local-spec-search'
STATE_DIR = '.spec-search'


def workspace_paths(workspace: Path) -> tuple[Path, Path]:
    root = workspace.expanduser().resolve()
    return root / STATE_DIR / 'config.json', root / STATE_DIR / 'index.sqlite'


def load_config(path: Path) -> dict:
    path = path.expanduser().resolve()
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ValueError(f'Configuration not found: {path}. Run spec-search init first.') from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON configuration: {path}: {exc}') from exc
    for key in ('source', 'database'):
        if not isinstance(data.get(key), str) or not data[key]:
            raise ValueError(f'Configuration field {key!r} is missing or invalid: {path}')
        data[key] = str(Path(data[key]).expanduser().resolve())
    return data


def save_config(path: Path, source: Path, database: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'schema_version': 1,
        'source': str(source.resolve()),
        'database': str(database.resolve()),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def install_vscode_config(workspace: Path, config_path: Path) -> Path:
    target = workspace.expanduser().resolve() / '.vscode' / 'mcp.json'
    if target.exists():
        try:
            root = json.loads(target.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f'Refusing to overwrite invalid JSON in {target}: {exc}. Fix it and rerun init.'
            ) from exc
        if not isinstance(root, dict):
            raise ValueError(f'Refusing to overwrite non-object JSON in {target}.')
    else:
        root = {}
    servers = root.setdefault('servers', {})
    if not isinstance(servers, dict):
        raise ValueError(f'Refusing to replace non-object "servers" in {target}.')
    servers[SERVER_NAME] = {
        'type': 'stdio',
        'command': sys.executable,
        'args': ['-m', 'spec_search.mcp_server', '--config', str(config_path.resolve())],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(root, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return target
