"""Regression: markdown outside the vault must not become graph nodes via symlinks."""
import os
import tempfile
import unittest

import kochi_layout


class TestVaultSymlink(unittest.TestCase):
    def test_symlink_outside_vault_is_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            vault = os.path.join(td, "vault")
            outside = os.path.join(td, "outside")
            os.makedirs(vault)
            os.makedirs(outside)
            with open(os.path.join(vault, "inside.md"), "w", encoding="utf-8") as f:
                f.write("# Inside Note\n")
            with open(os.path.join(outside, "secret.md"), "w", encoding="utf-8") as f:
                f.write("# Outside Secret\n")
            os.symlink(os.path.join(outside, "secret.md"), os.path.join(vault, "leak.md"))

            prev = kochi_layout.WIKI_DIR
            kochi_layout.WIKI_DIR = vault
            try:
                nodes, _ = kochi_layout.collect_pages()
            finally:
                kochi_layout.WIKI_DIR = prev

        self.assertIn("inside", nodes)
        self.assertNotIn("leak", nodes)
        self.assertNotIn("secret", nodes)

    def test_symlink_inside_vault_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            vault = os.path.join(td, "vault")
            sub = os.path.join(vault, "sub")
            os.makedirs(sub)
            target = os.path.join(sub, "target.md")
            with open(target, "w", encoding="utf-8") as f:
                f.write("# Target Note\n")
            os.symlink(target, os.path.join(vault, "link.md"))

            prev = kochi_layout.WIKI_DIR
            kochi_layout.WIKI_DIR = vault
            try:
                nodes, _ = kochi_layout.collect_pages()
            finally:
                kochi_layout.WIKI_DIR = prev

        self.assertIn("link", nodes)
        self.assertEqual(nodes["link"]["label"], "Target Note")


if __name__ == "__main__":
    unittest.main()
