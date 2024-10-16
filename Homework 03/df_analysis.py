import sys
import json
from collections import namedtuple

from form_blocks import form_blocks
import cfg

Analysis = namedtuple('Analysis', ['forward', 'init', 'merge', 'transfer'])

def union(sets):
    out = set()
    for s in sets:
        out.update(s)
    return out

def intersection(sets):
    if not sets:
        return set()
    out = set(sets[0])
    for s in sets[1:]:
        out.intersection_update(s)
    return out

def df_worklist(blocks, analysis):
    preds, succs = cfg.edges(blocks)

    if analysis.forward:
        first_block = list(blocks.keys())[0]
        in_edges = preds
        out_edges = succs
    else:
        first_block = list(blocks.keys())[-1]
        in_edges = succs
        out_edges = preds

    in_ = {first_block: analysis.init}
    out = {node: analysis.init for node in blocks}

    worklist = list(blocks.keys())
    while worklist:
        node = worklist.pop(0)

        inval = analysis.merge(list(out[n] for n in in_edges[node]))
        in_[node] = inval

        outval = analysis.transfer(node, blocks[node], inval)

        if outval != out[node]:
            out[node] = outval
            worklist += out_edges[node]

    return (in_, out) if analysis.forward else (out, in_)

def fmt(val):
    if isinstance(val, set):
        return ', '.join(sorted(map(str, val))) if val else '∅'
    elif isinstance(val, dict):
        return ', '.join(f'{k}: {v}' for k, v in sorted(val.items())) if val else '∅'
    else:
        return str(val)

def run_df(bril, analysis):
    for func in bril['functions']:
        blocks = cfg.block_map(form_blocks(func['instrs']))
        cfg.add_terminators(blocks)

        in_, out = df_worklist(blocks, analysis)
        for block in blocks:
            print(f'{block}:')
            print(f'  in:  {fmt(in_[block])}')
            print(f'  out: {fmt(out[block])}')

def gen_liveness(block):
    """Variables that are read before they are written in the block.
    """
    defined = set()  # Locally defined.
    used = set()
    for i in block:
        used.update(v for v in i.get('args', []) if v not in defined)
        if 'dest' in i:
            defined.add(i['dest'])
    return used

def kill_liveness(block):
    return {i['dest'] for i in block if 'dest' in i}

def gen_vbe(block):
    expressions = set()
    for instr in block:
        if 'args' in instr and len(instr['args']) > 1:
            expressions.add((instr['op'], tuple(instr['args'])))
    return expressions

def kill_vbe(block):
    return {expr for expr in gen_vbe(block) if any(arg in kill_liveness(block) for arg in expr[1])}

def gen_reaching_defs(label, block):
    return {(instr['dest'], label) for instr in block if 'dest' in instr}

def kill_reaching_defs(block):
    return {(instr['dest'], None) for instr in block if 'dest' in instr}

def gen_available_expr(block):
    return gen_vbe(block)

def kill_available_expr(block):
    return kill_vbe(block)

ANALYSES = {
    'liveness': Analysis(
        forward=False,
        init=set(),
        merge=union,
        transfer=lambda label, block, out: gen_liveness(block).union(out - kill_liveness(block))
    ),
    'vbe': Analysis(
        forward=False,
        init=set(),
        merge=intersection,
        transfer=lambda label, block, out: gen_vbe(block).union(out - kill_vbe(block))
    ),
    'reaching_defs': Analysis(
        forward=True,
        init=set(),
        merge=union,
        transfer=lambda label, block, in_: gen_reaching_defs(label, block).union(
            {(var, l) for (var, l) in in_ if (var, None) not in kill_reaching_defs(block)}
        )
    ),
    'available_expr': Analysis(
        forward=True,
        init=set(),
        merge=intersection,
        transfer=lambda label, block, in_: gen_available_expr(block).union(in_ - kill_available_expr(block))
    )
}

if __name__ == '__main__':
    bril = json.load(sys.stdin)
    run_df(bril, ANALYSES[sys.argv[1]])