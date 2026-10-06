#!/usr/bin/env python3
"""
kochi_layout.py — Fibonacci/phi spatial layout + centrality + Louvain communities for KOCHI wiki.

Layout algorithm: Fibonacci sphere (golden angle / phyllotaxis)
  - Community centroids: outer Fibonacci sphere (Manu decision: phi layout over FA2)
  - Nodes within community: inner Fibonacci sphere around centroid
  - Produces the "dendrite / tree branches" aesthetic — clusters as organic orbs in phi space

Deps: pip install networkx pyyaml python-louvain
      (python-louvain optional — falls back to networkx community)

Run from KOCHI/ directory:
    python3 ui/kochi_layout.py
Output: ui/kochi-graph.json
"""

import os
import re
import json
import math
import sys

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not found. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    import networkx as nx
except ImportError:
    print("ERROR: networkx not found. Run: pip install networkx", file=sys.stderr)
    sys.exit(1)

_DEFAULT_WIKI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample-wiki')
WIKI_DIR = os.environ.get('KOCHI_WIKI_DIR') or _DEFAULT_WIKI_DIR
OUT_JSON  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kochi-graph.json')

META_FILES = {'index.md', 'log.md', 'hot.md'}

WIKILINK_RE   = re.compile(r'\[\[([^\]|#\[]+)(?:\|[^\]]+)?\]\]')
MDLINK_RE     = re.compile(r'\[[^\]]*\]\(([^)#]+\.md)\)')
HEADING_RE    = re.compile(r'^#\s+(.+)$', re.MULTILINE)
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)

# ── Golden ratio constants ────────────────────────────────────────────────────
PHI          = (1 + math.sqrt(5)) / 2          # ≈ 1.6180…
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))    # ≈ 2.3999… rad ≈ 137.508°


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> dict:
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def extract_wikilinks(content: str) -> list:
    return [slug.strip().lower() for slug in WIKILINK_RE.findall(content) if slug.strip()]


def extract_markdown_links(content: str) -> list:
    slugs = []
    for target in MDLINK_RE.findall(content):
        base = os.path.basename(target.strip())
        if base.lower().endswith('.md'):
            slugs.append(os.path.splitext(base)[0].lower())
    return slugs


def first_heading(content: str) -> str:
    m = HEADING_RE.search(content)
    return m.group(1).strip() if m else ''


def collect_pages() -> tuple:
    nodes: dict = {}
    edges: list = []

    for root, dirs, files in os.walk(WIKI_DIR):
        dirs[:] = [d for d in dirs if d not in {'.obsidian'}]
        for fname in sorted(files):
            if not fname.endswith('.md') or fname in META_FILES:
                continue
            path = os.path.join(root, fname)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            has_fm = bool(FRONTMATTER_RE.match(content))
            fm = parse_frontmatter(content) if has_fm else {}

            if has_fm:
                if not fm or 'type' not in fm:
                    continue
                node_id = os.path.splitext(fname)[0].lower()
                ntype   = str(fm.get('type', 'concept'))
                label   = str(fm.get('title', node_id))
                summary = str(fm.get('summary', ''))[:200]
                tags    = fm.get('tags', []) or []
                body_start = content.find('\n---', 3)
                body = content[body_start:] if body_start != -1 else content
            else:
                node_id = os.path.splitext(fname)[0].lower()
                ntype   = 'concept'
                label   = first_heading(content) or os.path.splitext(fname)[0]
                summary = ''
                tags    = []
                body = content

            nodes[node_id] = {
                'id':          node_id,
                'label':       label,
                'type':        ntype,
                'entity_kind': str(fm.get('entity_kind', '')) if ntype == 'entity' else '',
                'summary':     summary,
                'tags':        tags,
            }

            if has_fm:
                # Related frontmatter wikilinks
                related = fm.get('related', [])
                if isinstance(related, list):
                    for item in related:
                        if isinstance(item, str):
                            slug = re.sub(r'^\[\[|\]\]$', '', item)
                            slug = slug.split('|')[0].split('#')[0].strip().lower()
                            if slug:
                                edges.append((node_id, slug))

            for link in extract_wikilinks(body):
                if link != node_id:
                    edges.append((node_id, link))
            if not has_fm:
                for link in extract_markdown_links(body):
                    if link != node_id:
                        edges.append((node_id, link))

    return nodes, edges


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph(nodes: dict, edges: list) -> nx.Graph:
    G = nx.Graph()
    for nid in nodes:
        G.add_node(nid)
    for src, dst in edges:
        if src in nodes and dst in nodes and src != dst:
            G.add_edge(src, dst)
    return G


# ── Fibonacci / Phi layout ────────────────────────────────────────────────────

def fibonacci_sphere(n: int, radius: float = 1.0) -> list:
    """
    Distribute n points on a sphere using the golden angle / Fibonacci method.
    Produces the phyllotaxis (sunflower seed) pattern in 3D.
    Mathematically optimal: maximises minimum angular distance between any two points.
    """
    positions = []
    for i in range(n):
        # Evenly spaced polar angles (avoid singularity at poles with +0.5 offset)
        theta = math.acos(max(-1.0, min(1.0, 1 - 2 * (i + 0.5) / max(n, 1))))
        # Golden angle azimuthal — creates the phi-spiral
        phi = GOLDEN_ANGLE * i
        x = radius * math.sin(theta) * math.cos(phi)
        y = radius * math.sin(theta) * math.sin(phi)
        z = radius * math.cos(theta)
        positions.append((x, y, z))
    return positions


def phi_layout(G: nx.Graph, partition: dict) -> dict:
    """
    Place nodes using nested Fibonacci spheres:
      Outer sphere: community centroids (large radius)
      Inner sphere: nodes within each community (radius ∝ √community_size)

    Result: organic dendritic clusters arranged in phi-optimal space.
    Deterministic, no iteration needed, always beautiful.
    """
    # Group nodes by community
    comm_nodes: dict = {}
    for nid, comm in partition.items():
        comm_nodes.setdefault(comm, []).append(nid)

    # Sort communities largest → smallest
    sorted_comms = sorted(comm_nodes.keys(), key=lambda c: len(comm_nodes[c]), reverse=True)
    n_comms = len(sorted_comms)

    # Outer Fibonacci sphere for community centroids
    OUTER_RADIUS = 280.0
    centroid_pts = fibonacci_sphere(n_comms, radius=OUTER_RADIUS)

    pos = {}

    for i, comm_id in enumerate(sorted_comms):
        cx, cy, cz = centroid_pts[i]
        nodes_in_comm = comm_nodes[comm_id]

        # Sort: highest-degree nodes closest to centroid (most connected = center of cluster)
        nodes_in_comm.sort(key=lambda nid: G.degree(nid), reverse=True)

        n = len(nodes_in_comm)

        if n == 1:
            pos[nodes_in_comm[0]] = (cx, cy, cz)
            continue

        # Inner Fibonacci sphere; radius grows with √n for consistent density
        INNER_RADIUS = max(18.0, math.sqrt(n) * 13.0)
        inner_pts = fibonacci_sphere(n, radius=INNER_RADIUS)

        # Rotate inner sphere to align its "north pole" toward the outer centroid direction
        # (so clusters point outward like branches from a centre)
        # Simple: just translate; Three.js rotation takes care of the 3D aesthetics
        for j, nid in enumerate(nodes_in_comm):
            ix, iy, iz = inner_pts[j]
            pos[nid] = (cx + ix, cy + iy, cz + iz)

    return pos


# ── Centrality & communities ──────────────────────────────────────────────────

def compute_centrality(G: nx.Graph) -> tuple:
    print("  Computing betweenness centrality...", flush=True)
    deg = dict(G.degree())
    btw = nx.betweenness_centrality(G, normalized=True)
    return deg, btw


def compute_communities(G: nx.Graph, seed: int = 42) -> dict:
    print("  Computing Louvain communities...", flush=True)

    try:
        import community as community_louvain
        p = community_louvain.best_partition(G, random_state=seed)
        print(f"  → python-louvain: {len(set(p.values()))} communities", flush=True)
        return p
    except ImportError:
        pass

    try:
        from networkx.algorithms.community import louvain_communities
        comms = louvain_communities(G, seed=seed)
        p = {}
        for i, comm in enumerate(sorted(comms, key=len, reverse=True)):
            for node in comm:
                p[node] = i
        print(f"  → networkx louvain: {len(comms)} communities", flush=True)
        return p
    except (ImportError, AttributeError):
        pass

    try:
        from networkx.algorithms.community import greedy_modularity_communities
        comms = list(greedy_modularity_communities(G))
        p = {}
        for i, comm in enumerate(sorted(comms, key=len, reverse=True)):
            for node in comm:
                p[node] = i
        print(f"  → greedy modularity: {len(comms)} communities", flush=True)
        return p
    except Exception:
        pass

    print("  → Fallback: all nodes in community 0", flush=True)
    return {nid: 0 for nid in G.nodes()}


# ── Assembly ──────────────────────────────────────────────────────────────────

def assemble(nodes, edges, G, pos, deg, btw, partition):
    out_nodes = []
    for nid, data in nodes.items():
        p = pos.get(nid, (0.0, 0.0, 0.0))
        out_nodes.append({
            'id':          nid,
            'label':       data['label'],
            'type':        data['type'],
            'entity_kind': data.get('entity_kind', ''),
            'summary':     data['summary'],
            'tags':        data['tags'],
            'degree':      int(deg.get(nid, 0)),
            'centrality':  round(float(btw.get(nid, 0.0)), 6),
            'community':   int(partition.get(nid, 0)),
            'x': round(float(p[0]), 2),
            'y': round(float(p[1]), 2),
            'z': round(float(p[2]), 2),
        })

    out_nodes.sort(key=lambda n: n['centrality'], reverse=True)

    seen: set = set()
    out_links = []
    for src, dst in edges:
        if src in nodes and dst in nodes and src != dst:
            key = (min(src, dst), max(src, dst))
            if key not in seen:
                seen.add(key)
                out_links.append({'source': src, 'target': dst})

    return {'nodes': out_nodes, 'links': out_links}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("KOCHI Phi Layout Builder")
    print("=" * 40)
    print(f"  Golden ratio φ = {PHI:.6f}")
    print(f"  Golden angle  = {math.degrees(GOLDEN_ANGLE):.4f}°")
    print()

    print("Collecting wiki pages...")
    nodes, edges = collect_pages()
    print(f"  → {len(nodes)} pages, {len(edges)} raw wikilinks")

    print("Building graph...")
    G = build_graph(nodes, edges)
    print(f"  → {G.number_of_nodes()} nodes, {G.number_of_edges()} unique edges")

    deg, btw  = compute_centrality(G)
    partition = compute_communities(G)

    print(f"Computing phi/Fibonacci spatial layout...")
    pos = phi_layout(G, partition)
    print(f"  → {len(pos)} nodes positioned (phi-optimal, deterministic)")

    print("Assembling output...")
    output = assemble(nodes, edges, G, pos, deg, btw, partition)

    n_nodes = len(output['nodes'])
    n_links = len(output['links'])
    n_comms = len(set(n['community'] for n in output['nodes']))
    top5    = [n['label'] for n in output['nodes'][:5]]
    n_ppl   = sum(1 for n in output['nodes'] if n.get('entity_kind') == 'person')

    print(f"\nResults:")
    print(f"  Nodes:         {n_nodes}  (incl. {n_ppl} person entities with avatars)")
    print(f"  Links:         {n_links}")
    print(f"  Communities:   {n_comms}")
    print(f"  Top-5 nodes:   {', '.join(top5)}")

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, separators=(',', ':'), ensure_ascii=False)

    size_kb = os.path.getsize(OUT_JSON) / 1024
    print(f"\nWritten: {OUT_JSON} ({size_kb:.0f} KB)")
    print("Rebuild HTML: python3 ui/kochi_layout.py && python3 -c \"...embed script...\"")


if __name__ == '__main__':
    main()
