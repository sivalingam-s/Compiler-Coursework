import json
import sys


def count_add_instrs(bril_program):

    count = 0
    print = 0
    for func in bril_program['functions']:
        for instr in func['instrs']:
            if 'op' in instr:
                if instr['op'] == 'add':
                    count += 1

    return count

def count_print_instrs(bril_program):

    printcount = 0
    for func in bril_program['functions']:
        for instr in func['instrs']:
            if 'op' in instr:
                if instr['op'] == 'print':
                    printcount += 1
                    
    return printcount

if __name__ == "__main__":

    json_file = "test/mat-inv.json"
    with open(json_file,'r') as f:
        bril_program = json.load(f)
    count = count_add_instrs(bril_program)
    print(f"Number of add instructions in addsqevenodd.json file : {count}")
    printcount = count_print_instrs(bril_program)
    print(f"Number of print instructions in addsqevenodd.json file : {printcount}")

