"""Regression: graph JSON in #kd cannot close the script element."""
import json
import os
import re
import tempfile
import unittest

import kochi_layout


class TestEmbedEscape(unittest.TestCase):
    def test_script_breakout_in_label_round_trips(self):
        payload = "</script><script>alert(1)</script>"
        graph = {
            "nodes": [
                {
                    "id": "x",
                    "label": payload,
                    "type": "note",
                    "summary": "",
                    "degree": 0,
                    "centrality": 0.0,
                    "community": 0,
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                }
            ],
            "links": [],
        }
        graph_json = json.dumps(graph)
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template = os.path.join(repo, "kochi-wiki-template.html")

        with tempfile.TemporaryDirectory() as td:
            graph_path = os.path.join(td, "graph.json")
            out_path = os.path.join(td, "out.html")
            with open(graph_path, "w", encoding="utf-8") as f:
                f.write(graph_json)
            kochi_layout.embed_wiki_html(template, out_path, graph_path)
            with open(out_path, encoding="utf-8") as f:
                html = f.read()

        m = re.search(
            r'<script type="application/json" id="kd">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "missing #kd block")
        embedded = m.group(1)
        self.assertNotIn("</script><script>", embedded)
        self.assertIn("\\u003c", embedded)
        restored = json.loads(embedded)
        self.assertEqual(restored["nodes"][0]["label"], payload)


if __name__ == "__main__":
    unittest.main()
