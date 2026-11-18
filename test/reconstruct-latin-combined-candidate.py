#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the combined-candidate stage chain."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/reconstruct-latin-combined-candidate.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class FakeModule:
    """Each stage appends its name; the attribution stage writes under a directory."""
    def __init__(self, name): self.name = name
    def prepare(self, candidate, headers, lexica, *rest):
        output = rest[1] if self.name == 'recover-latin-editor-attributions' else rest[0]
        data = candidate.read_bytes() + self.name.encode() + (rest[-1].encode() if isinstance(rest[-1], str) else b'') + b'\n'
        if self.name == 'recover-latin-editor-attributions':
            output.mkdir(); output = output / 'after.stems'
        output.write_bytes(data)
        return {'counts': {'touched': 1}, 'output_sha256': hashlib.sha256(data).hexdigest()}


class Chain(unittest.TestCase):
    def test_stages_run_in_order_on_each_others_output(self):
        real = m.sibling
        def fake(name):
            if name in {'repair-latin-first-conjugation', 'recover-latin-initial-sense'}:
                return real(name)
            return FakeModule(name)
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory, patch.object(m, 'sibling', fake):
            p = Path(directory); candidate = p / 'candidate'; candidate.write_bytes(b':le:x\n')
            (p / 'lexica').mkdir(); (p / 'headers').write_bytes(b''); (p / 'filters').mkdir()
            report = m.prepare(candidate, p / 'headers', p / 'lexica', p / 'filters', p / 'out')
            self.assertEqual([s['stage'] for s in report['stages']], [name for name, _ in m.STAGES])
            final = (p / 'out/combined.stems').read_bytes()
            self.assertTrue(final.startswith(b':le:x\nrecover-latin-editor-attributions\n'))
            self.assertIn(b'recover-latin-backlinked-present-classesbacklink\n', final)
            self.assertIn(b'recover-latin-backlinked-present-classesquotation\n', final)
            self.assertEqual(report['output_sha256'], hashlib.sha256(final).hexdigest())
            self.assertEqual(report['stages'][0]['input_sha256'], hashlib.sha256(b':le:x\n').hexdigest())
            for earlier, later in zip(report['stages'], report['stages'][1:]):
                self.assertEqual(earlier['output_sha256'], later['input_sha256'])
            self.assertEqual((p / 'out/combined.stems').stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                m.prepare(candidate, p / 'headers', p / 'lexica', p / 'filters', p / 'out')

    def test_private_output_boundary(self):
        with self.assertRaises(ValueError):
            m.prepare(Path('candidate'), Path('headers'), Path('lexica'), Path('filters'), SCRIPT.parents[1] / 'inside')


if __name__ == '__main__':
    unittest.main()
