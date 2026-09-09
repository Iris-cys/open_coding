"""Command-line interface for indexing, searching, and VS Code setup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from .config import install_vscode_config, load_config, save_config, workspace_paths
from .retriever import Retriever, VERSION, build


def emit(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def resolve_database(args: argparse.Namespace) -> Path:
    if getattr(args, 'db', None):
        return Path(args.db).expanduser().resolve()
    config, _ = workspace_paths(Path(getattr(args, 'workspace', '.')))
    return Path(load_config(config)['database'])


def cmd_init(args: argparse.Namespace) -> int:
    source = Path(args.pdf).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f'PDF not found: {source}')
    if source.suffix.lower() != '.pdf':
        raise ValueError(f'Only text-layer PDF files are supported in this release: {source}')
    workspace = Path(args.workspace).expanduser().resolve()
    config, database = workspace_paths(workspace)
    result = build(source, database)
    save_config(config, source, database)
    vscode = None if args.no_vscode else install_vscode_config(workspace, config)
    emit({
        'status': 'ready',
        'version': VERSION,
        'source': str(source),
        'database': str(database),
        'index': result,
        'vscode_mcp': str(vscode) if vscode else None,
        'next': 'Reload VS Code, trust local-spec-search, then ask the agent to search the indexed PDF.',
    })
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    database = resolve_database(args)
    engine = Retriever(database)
    try:
        out = engine.search(args.query, args.k)
    finally:
        engine.close()
    if not args.full:
        for item in out['results']:
            item.pop('context', None)
    emit(out)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    config, _ = workspace_paths(Path(args.workspace))
    checks = {'python': sys.version.split()[0], 'package_version': VERSION}
    try:
        data = load_config(config)
        source = Path(data['source'])
        database = Path(data['database'])
        checks.update({
            'config': str(config),
            'config_ok': True,
            'source_exists': source.is_file(),
            'database_exists': database.is_file(),
        })
        engine = Retriever(database)
        try:
            checks['index_version'] = engine.meta.get('version')
            checks['source_sha256'] = engine.meta.get('sha256')
            checks['indexed_pages'] = int(engine.meta.get('pages', 0))
        finally:
            engine.close()
        vscode = Path(args.workspace).expanduser().resolve() / '.vscode' / 'mcp.json'
        checks['vscode_mcp_exists'] = vscode.is_file()
        checks['status'] = 'healthy' if all(
            checks[x] for x in ('source_exists', 'database_exists', 'vscode_mcp_exists')
        ) else 'needs_attention'
    except (ValueError, OSError, sqlite3.DatabaseError) as exc:
        checks.update({'status': 'broken', 'error': str(exc)})
    emit(checks)
    return 0 if checks['status'] == 'healthy' else 1


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog='spec-search',
        description='Offline evidence search and MCP access for a long technical PDF.',
    )
    ap.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    sub = ap.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Build an index and configure VS Code MCP.')
    init.add_argument('pdf', help='Path to a text-layer PDF.')
    init.add_argument('--workspace', default='.', help='VS Code workspace (default: current directory).')
    init.add_argument('--no-vscode', action='store_true', help='Build only; do not edit .vscode/mcp.json.')
    init.set_defaults(func=cmd_init)
    search = sub.add_parser('search', help='Search evidence from the configured index.')
    search.add_argument('query')
    search.add_argument('--workspace', default='.')
    search.add_argument('--db', help='Use an explicit index instead of workspace configuration.')
    search.add_argument('-k', type=int, choices=range(1, 11), default=3, metavar='1..10')
    search.add_argument('--full', action='store_true', help='Include full neighboring-page text.')
    search.set_defaults(func=cmd_search)
    doctor = sub.add_parser('doctor', help='Check configuration, source, index, and VS Code setup.')
    doctor.add_argument('--workspace', default='.')
    doctor.set_defaults(func=cmd_doctor)
    return ap


def main() -> None:
    args = parser().parse_args()
    try:
        code = args.func(args)
    except (ValueError, OSError, sqlite3.DatabaseError) as exc:
        print(f'spec-search: {exc}', file=sys.stderr)
        code = 2
    raise SystemExit(code)
