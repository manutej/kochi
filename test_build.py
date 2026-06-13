#!/usr/bin/env python3
"""Behavioral tests for fix E01: KOCHI_WIKI_DIR env var, fail on 0 pages, pinned CDN.

Run with: python3 -m unittest test_build -v
Stdlib only (unittest + subprocess + tempfile) — no pytest required.
"""

import json
import os
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.abspath(__file__))
LAYOUT = os.path.join(REPO, 'kochi_layout.py')
BUILD = os.path.join(REPO, 'build.sh')
TEMPLATE = os.path.join(REPO, 'kochi-wiki-template.html')
OUT_JSON = os.path.join(REPO, 'kochi-graph.json')

PAGE = """---
type: concept
title: Solo Page
summary: a single test page
---

Body with no links.
"""


def run_layout(wiki_dir):
    env = {**os.environ, 'KOCHI_WIKI_DIR': wiki_dir}
    return subprocess.run(
        ['python3', LAYOUT], cwd=REPO, env=env,
        capture_output=True, text=True, timeout=120,
    )


class TestZeroPagesFailsBuild(unittest.TestCase):
    def test_empty_dir_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_layout(d)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn('ERROR: 0 pages', r.stderr)

    def test_nonexistent_dir_exits_nonzero(self):
        r = run_layout('/no/such/dir/kochi-test-xyz')
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn('ERROR: 0 pages', r.stderr)

    def test_dir_with_md_but_no_frontmatter_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'page.md'), 'w') as f:
                f.write('# No frontmatter here\n')
            r = run_layout(d)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn('ERROR: 0 pages', r.stderr)

    def test_build_sh_propagates_failure(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, 'out.html')
            r = subprocess.run(
                ['bash', BUILD, d, out], cwd=REPO,
                capture_output=True, text=True, timeout=120,
            )
            self.assertNotEqual(r.returncode, 0, msg=r.stdout + r.stderr)
            self.assertFalse(os.path.exists(out),
                             'build.sh must not emit HTML when layout fails')


class TestEnvVarWikiDir(unittest.TestCase):
    def test_reads_configured_path(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'solo-page.md'), 'w') as f:
                f.write(PAGE)
            r = run_layout(d)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        with open(OUT_JSON) as f:
            graph = json.load(f)
        ids = [n['id'] for n in graph['nodes']]
        self.assertEqual(ids, ['solo-page'],
                         'graph must be built from KOCHI_WIKI_DIR, not the default path')

    def test_sample_wiki_happy_path(self):
        r = run_layout(os.path.join(REPO, 'sample-wiki'))
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        with open(OUT_JSON) as f:
            graph = json.load(f)
        self.assertEqual(len(graph['nodes']), 5, msg=graph)


class TestCdnPin(unittest.TestCase):
    def test_3d_force_graph_is_version_pinned(self):
        with open(TEMPLATE) as f:
            html = f.read()
        self.assertIn('3d-force-graph@1.80.0/dist/3d-force-graph.min.js', html)
        self.assertNotIn('npm/3d-force-graph/dist', html,
                         'unpinned 3d-force-graph CDN URL must not reappear')


if __name__ == '__main__':
    unittest.main(verbosity=2)
