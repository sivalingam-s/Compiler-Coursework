import json
import sys
from collections import namedtuple

Value = namedtuple('Value', ['op', 'args'])

class Numbering(dict):
    def __init__(self, init={}):
        super(Numbering, self).__init__(init)
        self._next_fresh = 0

    def _fresh(self):
        n = self._next_fresh
        self._next_fresh = n + 1
        return n

    def add(self, key):
        n = self._fresh()
        self[key] = n
        return n

def last_writes(instrs):
    out = [False] * len(instrs)
    seen = set()
    for idx, instr in reversed(list(enumerate(instrs))):
        if 'dest' in instr:
            dest = instr['dest']
            if dest not in seen:
                out[idx] = True
                seen.add(dest)
    return out

def read_first(instrs):
    read = set()
    written = set()
    for instr in instrs:
        read.update(set(instr.get('args', [])) - written)
        if 'dest' in instr:
            written.add(instr['dest'])
    return read

def lvn_block(block, lookup):
    var2num = Numbering()
    value2num = {}
    num2vars = {}

    for var in read_first(block):
        num = var2num.add(var)
        num2vars[num] = [var]

    for instr, last_write in zip(block, last_writes(block)):
        argvars = instr.get('args', [])
        argnums = tuple(var2num[var] for var in argvars)

        if 'args' in instr:
            instr['args'] = [num2vars[n][0] for n in argnums]

        val = None
        if 'dest' in instr and 'args' in instr:
            val = Value(instr['op'], argnums)
            num = lookup(value2num, val)
            if num is not None:
                var2num[instr['dest']] = num
                instr.update({
                    'op': 'id',
                    'args': [num2vars[num][0]],
                })
                num2vars[num].append(instr['dest'])
                continue

        if 'dest' in instr:
            newnum = var2num.add(instr['dest'])
            var = 'lvn.{}'.format(newnum) if not last_write else instr['dest']
            num2vars[newnum] = [var]
            instr['dest'] = var

            value2num[val] = newnum

def _lookup(value2num, value):
    return value2num.get(value)

def lvn(bril):
    for func in bril['functions']:
        blocks = func['instrs']
        lvn_block(blocks, lookup=_lookup)
        func['instrs'] = blocks

if __name__ == '__main__':
    bril = json.load(sys.stdin)
    lvn(bril)
    json.dump(bril, sys.stdout, indent=2, sort_keys=True)
