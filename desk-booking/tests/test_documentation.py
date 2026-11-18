"""Documentation builds must reject changed code and mismatched manuals."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('desk_manuals',ROOT/'documentation.py')
docs=importlib.util.module_from_spec(spec);spec.loader.exec_module(docs)


class DocumentationTests(unittest.TestCase):
    def test_text_digest_accepts_platform_line_endings_but_detects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'source.py'
            path.write_bytes(b'first\nsecond\n')
            expected = docs.content_digest(path)
            path.write_bytes(b'first\r\nsecond\r\n')
            self.assertEqual(expected, docs.content_digest(path))
            path.write_bytes(b'first\r\nchanged\r\n')
            self.assertNotEqual(expected, docs.content_digest(path))

    def test_review_matches_actual_sources_and_outputs(self):
        docs.check()

    def test_code_change_blocks_packaging(self):
        with patch.object(docs,'sources',return_value={'changed':'source'}):
            with self.assertRaises(SystemExit):docs.check()

    def test_changed_source_or_html_requires_review(self):
        for suffix in ('.md','.html'):
            with tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'docs';shutil.copytree(docs.DOCS,target)
                path=target/('benutzer'+suffix)
                path.write_text(path.read_text(encoding='utf-8')+'Changed',encoding='utf-8')
                reviewed_sources=json.loads((target/'review.json').read_text(encoding='utf-8'))['sources']
                with patch.object(docs,'DOCS',target), patch.object(docs,'sources',return_value=reviewed_sources):
                    with self.assertRaises(SystemExit):docs.check()

    def test_static_manual_does_not_execute_embedded_html(self):
        html=docs.inline('<script>alert(1)</script> **Test** [Quelle](https://example.invalid/test)')
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('<strong>Test</strong>',html)
        self.assertIn('href="https://example.invalid/test"',html)
