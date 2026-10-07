#!/usr/bin/env python3
"""Generate a KOCHI-compatible wiki tree from glue lego.json (stdlib only)."""

import json
import os
import shutil
import sys

FORBIDDEN = frozenset({'index.md', 'log.md', 'hot.md'})


def yaml_list(items: list) -> str:
    if not items:
        return '[]'
    inner = ', '.join(json.dumps(x) for x in items)
    return f'[{inner}]'


def main() -> int:
    if len(sys.argv) != 3:
        print(f'usage: {sys.argv[0]} <lego.json> <outdir>', file=sys.stderr)
        return 2

    lego_path, outdir = sys.argv[1], sys.argv[2]
    with open(lego_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    blocks = {b['id']: b for b in data.get('blocks', [])}
    joints = data.get('joints', [])
    outgoing: dict[str, list] = {bid: [] for bid in blocks}
    for j in joints:
        fr = j.get('from')
        if fr in outgoing:
            outgoing[fr].append(j)

    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)

    for bid, block in blocks.items():
        fname = f'{bid}.md'
        if fname.lower() in FORBIDDEN:
            print(f'refuse to write forbidden name: {fname}', file=sys.stderr)
            return 1

        lane = block.get('lane', '')
        maturity = block.get('maturity', '')
        one_line = block.get('oneLine', '')
        title = bid
        tags = [lane, maturity] if lane or maturity else []

        lines = [
            '---',
            f'type: repo',
            f'title: {json.dumps(title)}',
            f'summary: {json.dumps(one_line)}',
            f'tags: {yaml_list(tags)}',
            '---',
            '',
            f'# {title}',
            '',
            one_line,
            '',
            '## Joints',
            '',
        ]
        for j in sorted(outgoing[bid], key=lambda x: x.get('id', '')):
            to_id = j.get('to', '')
            label = j.get('label', '')
            status = j.get('status', '')
            lines.append(f'- [[{to_id}]] — {label} ({status})')

        path = os.path.join(outdir, fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines).rstrip() + '\n')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
