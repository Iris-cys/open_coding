import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import fitz

from spec_search.config import install_vscode_config, save_config, workspace_paths
from spec_search.retriever import Retriever, build


def create_pdf(path: Path) -> None:
    doc = fitz.open()
    texts = [
        'Front matter for Example Technical Specification.',
        'Function Level Reset (FLR) resets one Function without resetting the entire Link. '
        'Software initiates FLR and must wait for completion.',
        'Address Translation Services (ATS) lets a Function request translated addresses. '
        'An Invalidate Request requires an Invalidate Completion.',
        'Recovery retrains the Link after a speed change or error condition.',
    ]
    for text in texts:
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(72, 72, 520, 760), text, fontsize=12)
    doc.set_toc([
        [1, 'Section 1 Introduction', 1],
        [1, 'Section 2 Function Level Reset', 2],
        [1, 'Section 3 Address Translation Services', 3],
        [1, 'Section 4 Recovery', 4],
    ])
    doc.save(path)
    doc.close()


class EndToEndTests(unittest.TestCase):
    def test_build_search_reuse_and_abstention(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / 'spec.pdf'
            db = root / 'index.sqlite'
            create_pdf(pdf)
            first = build(pdf, db)
            second = build(pdf, db)
            self.assertFalse(first['reused'])
            self.assertTrue(second['reused'])

            engine = Retriever(db)
            try:
                answer = engine.search('怎么只复位一个 PCIe function？', 3)
                self.assertEqual(answer['status'], 'candidates')
                self.assertTrue(any('Function Level Reset' in row['excerpt'] for row in answer['results']))
                self.assertTrue(answer['results'][0]['context'][0]['text'])
                unknown = engine.search('ZQK9999 proprietary opcode', 3)
                self.assertEqual(unknown['status'], 'insufficient_evidence')
                self.assertEqual(unknown['results'], [])
            finally:
                engine.close()

    def test_vscode_config_merge_and_mcp_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / 'spec.pdf'
            create_pdf(pdf)
            config, db = workspace_paths(root)
            build(pdf, db)
            save_config(config, pdf, db)

            vscode = root / '.vscode' / 'mcp.json'
            vscode.parent.mkdir()
            vscode.write_text(json.dumps({'servers': {'existing': {'command': 'existing'}}}), encoding='utf-8')
            install_vscode_config(root, config)
            installed = json.loads(vscode.read_text(encoding='utf-8'))
            self.assertEqual(installed['servers']['existing']['command'], 'existing')
            server = installed['servers']['local-spec-search']
            self.assertEqual(server['type'], 'stdio')
            self.assertEqual(Path(server['command']).resolve(), Path(sys.executable).resolve())

            requests = [
                {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-03-26'}},
                {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
                {
                    'jsonrpc': '2.0',
                    'id': 3,
                    'method': 'tools/call',
                    'params': {'name': 'search_evidence', 'arguments': {'query': 'Function Level Reset', 'k': 2}},
                },
                {
                    'jsonrpc': '2.0',
                    'id': 4,
                    'method': 'tools/call',
                    'params': {'name': 'search_evidence', 'arguments': {'query': '\" OR *; DROP TABLE pages; --'}},
                },
            ]
            run = subprocess.run(
                [server['command'], *server['args']],
                input='\n'.join(json.dumps(x) for x in requests) + '\n',
                text=True,
                capture_output=True,
                timeout=30,
                check=True,
            )
            responses = {row['id']: row for row in map(json.loads, run.stdout.splitlines())}
            self.assertEqual(responses[1]['result']['protocolVersion'], '2025-03-26')
            self.assertEqual(
                {x['name'] for x in responses[2]['result']['tools']},
                {'search_evidence', 'read_pages'},
            )
            self.assertFalse(responses[3]['result']['isError'])
            self.assertFalse(responses[4]['result']['isError'])
            self.assertEqual(run.stderr, '')

    def test_cli_init_and_doctor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / 'spec.pdf'
            create_pdf(pdf)
            init = subprocess.run(
                [sys.executable, '-m', 'spec_search', 'init', str(pdf), '--workspace', str(root)],
                text=True,
                capture_output=True,
                timeout=30,
                check=True,
            )
            self.assertEqual(json.loads(init.stdout)['status'], 'ready')
            doctor = subprocess.run(
                [sys.executable, '-m', 'spec_search', 'doctor', '--workspace', str(root)],
                text=True,
                capture_output=True,
                timeout=30,
                check=True,
            )
            self.assertEqual(json.loads(doctor.stdout)['status'], 'healthy')

    def test_invalid_existing_mcp_config_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / '.vscode' / 'mcp.json'
            target.parent.mkdir()
            target.write_text('{ broken', encoding='utf-8')
            before = target.read_bytes()
            with self.assertRaisesRegex(ValueError, 'Refusing to overwrite invalid JSON'):
                install_vscode_config(root, root / '.spec-search' / 'config.json')
            self.assertEqual(target.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
