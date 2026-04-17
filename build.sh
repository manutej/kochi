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
with open('kochi-graph.json') as f: j=f.read()
with open('kochi-wiki-template.html') as f: t=f.read()
open('$OUT_HTML','w').write(t.replace('GRAPH_JSON_PLACEHOLDER',j))
print('Built: $OUT_HTML (' + str(len(open('$OUT_HTML').read())//1024) + 'KB)')
"

echo ""
echo "Done! Open: open $OUT_HTML"
