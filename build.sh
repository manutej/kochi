#!/usr/bin/env bash
# KOCHI build script — run from repo root
set -e

WIKI_DIR="${1:-./sample-wiki}"
OUT_HTML="${2:-kochi-wiki.html}"

echo "KOCHI Build"
echo "  Wiki: $WIKI_DIR"
echo "  Output: $OUT_HTML"
echo ""

# Check deps
python3 -c "import networkx, yaml" 2>/dev/null || {
  echo "Missing deps. Run: pip install networkx pyyaml python-louvain"
  exit 1
}

# Set WIKI_DIR override via env so kochi_layout.py can pick it up
KOCHI_WIKI_DIR="$WIKI_DIR" python3 kochi_layout.py

python3 -c "
import kochi_layout
kochi_layout.embed_wiki_html('kochi-wiki-template.html', '$OUT_HTML', 'kochi-graph.json')
import os
size_kb = os.path.getsize('$OUT_HTML') // 1024
print(f'Built: $OUT_HTML ({size_kb}KB)')
"

echo ""
echo "Done! Open: open $OUT_HTML"
