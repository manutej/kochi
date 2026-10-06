# KOCHI 故智 — Personal Knowledge Universe

> *故智 (kochi) — wisdom compounded from the ancients*

KOCHI is an open-source **3D knowledge graph viewer** for Obsidian/markdown wikis. Bring your own vault — KOCHI builds a stunning interactive graph from your local markdown files in minutes.

**[Live Demo →](https://deploy-pink-gamma.vercel.app)**

---

## What it does

- Parses any Obsidian vault (or flat markdown wiki) with YAML frontmatter
- Computes a **Fibonacci sphere / phi spatial layout** — organic dendritic clusters
- Renders a **3D interactive graph** with search, filters, reader panel, and autorotation
- Produces a single self-contained HTML file you can open offline or host anywhere

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/manutej/kochi
cd kochi

# 2. Install deps
pip install networkx pyyaml python-louvain

# 3. Build from a wiki folder (default: ./sample-wiki/)
#    bash build.sh /path/to/vault
bash build.sh
# → outputs kochi-wiki.html (graph JSON is embedded; no manual embed step)

# 4. Open
open kochi-wiki.html
```

## Wiki Schema

KOCHI reads any `.md` file with YAML frontmatter. Required fields:

```yaml
---
title: "My Concept"
type: concept          # entity | concept | source | hub | query
summary: "One-line description (≤200 chars)"
tags: [ai, research]
---
```

Optional fields per type:

| Type | Extra fields |
| --- | --- |
| `entity` | `entity_kind: person\|org\|product\|model` |
| `concept` | `confidence: high\|medium\|low`, `related: [[[link]]]` |
| `source` | `authors: []`, `date_read: YYYY-MM-DD`, `key_claims: []` |
| `hub` | `members: [[[link1]], [[link2]]]` |

See `sample-wiki/` for working examples.

## Controls

| Key / Action | Effect |
| --- | --- |
| Click node | Open reader panel |
| Drag | Orbit camera |
| Scroll | Zoom |
| `/` | Focus search |
| Space | Toggle rotation |
| Esc | Reset / close |
| ☾/☀ button | Dark / light mode |
| By Type / By Cluster | Color mode |

## Deployment

The output `kochi-wiki.html` is a single self-contained file. Deploy anywhere:

```bash
# Vercel (recommended)
npx vercel --prod

# Netlify drop
# → drag kochi-wiki.html to netlify.com/drop

# GitHub Pages
# → push kochi-wiki.html to gh-pages branch as index.html
```

## Architecture

- **Layout**: Fibonacci sphere (golden angle φ = 137.5°) — deterministic, organic, beautiful
- **Renderer**: [3d-force-graph](https://github.com/vasturiano/3d-force-graph) v1.80 (Three.js WebGL)
- **Communities**: Louvain algorithm (via networkx or python-louvain)
- **Centrality**: Betweenness centrality for node sizing
- **Output**: Single HTML ~400KB (smaller without large wikis)

## Privacy

This repo contains **zero personal wiki data**. The `sample-wiki/` directory has minimal fictional examples. Your own vault data stays local — only the built `kochi-wiki.html` (which embeds your JSON) gets shared if you deploy it.

## Roadmap (v2)

- [ ] 3D default + 2D toggle view
- [ ] Node hover: highlight neighbors, fade non-connected
- [ ] Click: zoom to subgraph with visible labels
- [ ] Full markdown reader with rendered body + expand
- [ ] Person avatar nodes (circular initials)
- [ ] AI assistant navigation layer (Graph RAG)

## License

MIT — fork, modify, build your own knowledge universe.

---

Built by [Manu Mulaveesala](https://cetiai.co) · CETI.AI
