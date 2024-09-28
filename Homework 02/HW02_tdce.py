import sys
import json
import itertools

# Instructions that terminate a basic block.
TERMINATORS = 'br', 'jmp', 'ret'


def new_blocks(instrs):
    cur_block = []

    for instr in instrs:
        if 'op' in instr:  
            cur_block.append(instr)

            if instr['op'] in TERMINATORS:
                yield cur_block
                cur_block = []

        else:  
            if cur_block:
                yield cur_block

            cur_block = [instr]

    if cur_block:
        yield cur_block


def delete_local(block):

    last_def = {}

    to_drop = set()
    for i, instr in enumerate(block):

        for var in instr.get('args', []):
            if var in last_def:
                del last_def[var]

        if 'dest' in instr:
            dest = instr['dest']
            if dest in last_def:

                to_drop.add(last_def[dest])
            last_def[dest] = i

    new = [instr for i, instr in enumerate(block)
                 if i not in to_drop]
    changed = len(new) != len(block)
    block[:] = new
    return changed


def delete_reassign(func):

    blocks = list(new_blocks(func['instrs']))
    changed = False
    for block in blocks:
        changed |= delete_local(block)
    func['instrs'] = list(itertools.chain(*blocks))
    return changed


if __name__ == '__main__':
    bril = json.load(sys.stdin)
    for func in bril['functions']:
        while delete_reassign(func):
            pass

    json.dump(bril, sys.stdout, indent=2, sort_keys=True)

