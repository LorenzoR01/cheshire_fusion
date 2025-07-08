import re
import sys
import csv
from typing import List, Optional
from collections import defaultdict

class Register:
    def __init__(self, id: Optional[str], value: Optional[str] = None):
        self.id = id
        self.value = value

    def __repr__(self):
        return f"Register(id={self.id}, value={self.value})"

class Instruction:
    def __init__(self, time: int, cycles: int, privilege: str, pc: str, mispredict: bool,
                 opcode: str, mnemonic: str, rd: Register, rs1: Register, rs2: Register,
                 imm_offset: Optional[str], memory_address: Optional[str]):
        self.time = time
        self.cycles = cycles
        self.privilege = privilege
        self.pc = pc
        self.mispredict = mispredict
        self.opcode = opcode
        self.mnemonic = mnemonic
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2
        self.imm_offset = imm_offset
        self.memory_address = memory_address

    def __repr__(self):
        return (f"Instruction(time={self.time}, cycles={self.cycles}, privilege='{self.privilege}', pc='{self.pc}', \n"
                f"mispredict={self.mispredict}, opcode='{self.opcode}', mnemonic='{self.mnemonic}', \n"
                f"rd={self.rd}, rs1={self.rs1}, rs2={self.rs2}, imm_offset={self.imm_offset}, \n"
                f"memory_address={self.memory_address})")

def parse_trace_line(line: str) -> Instruction:
    parts = line.split()

    time = int(parts[0].strip('ns'))
    cycles = int(parts[1])
    privilege = parts[2]
    pc = parts[3]
    mispredict = parts[4] == '1'
    opcode = parts[5]
    mnemonic = parts[6]

    # Extract operands field
    operands_end = 7
    for i in range(7, len(parts)):
        if not parts[i].endswith(','):
            operands_end = i + 1
            break

    operands = parts[7:operands_end]
    operands = [op.rstrip(',') for op in operands]

    rd, rs1, rs2, imm_offset = None, None, None, None

    if operands:
        if len(operands) == 2 and operands[1].isdigit():
            rd = operands[0]  # Handle c.li and similar instructions
            imm_offset = operands[1]
        else:
            if mnemonic in {'beqz', 'bne', 'beq', 'blt', 'bgt', 'ble', 'bge', 'bltu', 'bgtu', 'bgeu', 'bleu', 'bnez', 'bltz', 'bgtz', 'blez', 'bgez'}:
                # Branch instructions
                if len(operands) == 3:
                    rd = None
                    rs1 = operands[0]
                    rs2 = operands[1]
                else:
                    rd = None
                    rs1 = operands[0]
                    rs2 = None
            else:
                if re.match(r'^[a-zA-Z]+\d+$', operands[0]) or operands[0] in {'ra', 'sp', 'gp'}:
                    rd = operands[0]
                else:
                    rd = None
                for op in operands[1:]:
                    if re.match(r'^[a-zA-Z]+\d+$', op) or op in {'ra', 'sp', 'gp'}:  # Register (rs1 or rs2)
                        if rs1 is None:
                            rs1 = op
                        else:
                            rs2 = op
                    elif re.match(r'^-?\d+$', op):  # Immediate/Offset
                        imm_offset = op
                    elif re.match(r'-?\d+\([a-zA-Z]+\d+\)', op):  # Number(Register)
                        num, reg = re.findall(r'-?\d+|[a-zA-Z]+\d+', op)
                        rs1 = reg
                        imm_offset = num

    # Extract register values and memory address
    register_values = {}
    memory_address = None
    for i in range(operands_end, len(parts), 2):
        if i + 1 < len(parts):
            key, val = parts[i].strip(':'), parts[i + 1].lstrip(':')
            if key in {rd, rs1, rs2}:
                register_values[key] = val
            elif key == "VA" or key == "PA":
                memory_address = val

    # Assign values to register objects
    rd = Register(rd, register_values.get(rd)) if rd else Register(None)
    rs1 = Register(rs1, register_values.get(rs1)) if rs1 else Register(None)
    rs2 = Register(rs2, register_values.get(rs2)) if rs2 else Register(None)

    return Instruction(time, cycles, privilege, pc, mispredict, opcode, mnemonic, rd, rs1, rs2, imm_offset, memory_address)

def parse_trace_file(filename: str) -> List[Instruction]:
    instructions = []
    skip_next = False  # Flag to skip the next line
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if skip_next:  # If previous line was an Exception, skip this one
                skip_next = False
                continue
            if line.startswith("Exception"):  # Skip this line and the next one
                skip_next = True
                continue
            instructions.append(parse_trace_line(line))
    return instructions

def filter_benchmark_part(all_instructions):
    "Keep only benchmark part from a trace"
    filtered = []
    # re_csrr_minstret = re.compile(r"^csrr\s+\w\w,\s*minstret$")
    accepting = False
    for instr in all_instructions:
        # if re_csrr_minstret.search(instr.mnemo):
        if "32951073" in instr.opcode:
            accepting = not accepting
            continue
        if accepting:
            filtered.append(instr)
    return filtered

# Example Usage
# instructions = parse_trace_file("/home/ms_lridolfi/cheshire_fusion/tracelogs/trace_hart_0_crc32.log")
# for instr in instructions:
#     print(instr)


testname = sys.argv[1]
instructions = parse_trace_file("../tracelogs/trace_hart_0_"+testname+".log")
instructions = filter_benchmark_part(instructions)

excluded_mnemonics = {'csrr', 'jal', 'c.jr', 'jr',}
#  'ld', 'sd', 'lw', 'sw', 'c.lw', 'lbu', 'sbu', 'lb', 'sb', 'mul', 'mulhu'

stats = defaultdict(int)

instret = len(instructions)
print("Benchmark: "+testname, "Instructions: "+str(instret))
for very_old, old, young in zip(instructions, instructions[1:], instructions[2:]):
    if (very_old.mnemonic in excluded_mnemonics or old.mnemonic in excluded_mnemonics):
        continue
    if (very_old.rd.id is None):
        continue

    # check if both instructions are inside the same 64 bit aligned interval
    #if ((int(old.pc,16) - int(old.pc,16)%8)) != (int(young.pc,16) - int(young.pc,16)%8): # check if both instructions have pc inside the 64 bit interval
    #    continue
    #if (young.mnemonic[0:2] != "c."): # check if second instruction is fully contained inside the 64 bit interval
    #    if(int(young.pc,16) + 3 > (int(young.pc,16) - int(young.pc,16)%8) + 7): 
    #        continue

    if ((very_old.rd.id == old.rs1.id or very_old.rd.id == old.rs2.id) and (very_old.rd.id == old.rd.id or old.rd.id == None)):
        stats[f'{very_old.mnemonic}+{old.mnemonic}'] += 1
    # fusions with different rd
    #elif((very_old.rd.id == old.rs1.id or very_old.rd.id == old.rs2.id) and ((very_old.rd.id == young.rd.id) and (young.rs1.id != very_old.rd.id) and (young.rs2.id != very_old.rd.id))):
    #    stats[f'{very_old.mnemonic}+{old.mnemonic}'] += 1
    # non contiguous fusions
    #elif((very_old.rd.id == young.rs1.id or very_old.rd.id == young.rs2.id) and (very_old.rd.id == young.rd.id or young.rd.id == None) and old.rs1.id != very_old.rd.id and old.rs2.id != very_old.rd.id and old.rd.id != very_old.rd.id and not(old.mnemonic in excluded_mnemonics)):
    #    stats[f'{very_old.mnemonic}+{young.mnemonic}'] += 1

data = []

for i, (key, value) in enumerate(sorted(stats.items(), key=lambda item: item[1], reverse=True)):
    if i >= 10:
        break
    print(f"{key},{value},{100*value/instret:.2f}")
    data.append({'testname': testname, 'instructions': key, 'count': value, 'percentage': 100*value/instret})

with open('fusion_candidates.csv', 'a', newline='') as csvfile:
    fieldnames = ['testname', 'instructions', 'count', 'percentage']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writerows(data)
