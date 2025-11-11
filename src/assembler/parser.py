from typing import Tuple, List, Dict
import re

REGISTERS = {
    "r0": 0, "r1": 1, "r2": 2, "r3": 3,
    "r4": 4, "r5": 5, "r6": 6, "r7": 7,
    "sp": 7, "pc": 8
}

OPCODES = {
    "NOP":      0b00_0000, "HALT":      0b00_0001,
    "RET":      0b00_0010, "MOV":       0b00_0011,
    "ADD":      0b01_0000, "SUB":       0b01_0001,
    "MUL":      0b01_0010, "MULH":      0b01_0011,
    "AND":      0b01_0100, "OR":        0b01_0101,
    "XOR":      0b01_0110, "SHL":       0b01_0111,
    "ROL":      0b01_1000, "SHR":       0b01_1001,
    "ASR":      0b01_1010, "ROR":       0b01_1011,
    "CMP":      0b01_1100, "NOT":       0b01_1101,
    "NEG":      0b01_1110, "JMP":       0b100_000,
    "JZ":       0b100_001, "JEQ":       0b100_001,
    "JNZ":      0b100_010, "JNE":       0b100_010,
    "JLT":      0b100_011, "JGT":       0b100_100,
    "JC":       0b100_101, "JNC":       0b100_110,
    "CALL":     0b100_111, "LOADB":     0b101_000,
    "LOAD":     0b101_001, "STOREB":    0b101_010,
    "STORE":    0b101_011, "POPB":      0b101_100,
    "POP":      0b101_101, "PUSHB":     0b101_110,
    "PUSH":     0b101_111,
}

class Parser():
    def __init__(self, assembler):
        self.assembler = assembler
        self.filename = []
        self.line_num = {}
        self.pc = 0
        self.current_scope = None # Current global scope defined by the last global label
        self.imports = []

    def parse_file(self, program, filename):
        self.filename.append(filename)
        self.line_num[self.filename[-1]] = 1
        for line in program:
            self.parse_line(line)
            self.line_num[self.filename[-1]] += 1
        self.filename.pop() # When done, pop the filename to get the the previous one back (for imports/recursive file parsing)

        for import_filename in self.imports: # Handle @import directives at the end, so the code of the current file is at the beginning of the assembled binary
            self.imports.remove(import_filename)
            with open(import_filename, "r") as import_file:
                program = import_file.read().splitlines()
                self.parse_file(program, import_filename)

    def parse_line(self, line: str):
        line = line.split(';')[0].strip() # Strip comments & whitespace
        if not line: # Skip empty lines
            return
        tokens = re.findall(r'\[|\]|"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|[^\s,\[\]]+', line)
        if tokens[0].startswith('@'):
            self.parse_directive(tokens)
        elif tokens[0].endswith(':'):
            self.parse_label(tokens)
        else:
            self.parse_instruction(tokens)

    def parse_instruction(self, tokens: List[str]):
        mnemonic = tokens[0].upper()
        if mnemonic not in OPCODES:
            raise SyntaxError(f"Unknown instruction '{mnemonic}' (line {self.line_num[self.filename[-1]]})")

        instruction = { "mnemonic": mnemonic, "address": self.pc }
        operands = tokens[1:]
        if operands:
            operands, addressing_mode = self.parse_operands(operands)
            instruction["operands"] = operands
            instruction["addressing_mode"] = addressing_mode
        instruction["length"] = self.get_instruction_length(instruction)

        self.assembler.program.append({"type": "instruction", "value": instruction})
        self.pc += instruction["length"]

    def parse_operands(self, operands: List[str]) -> Tuple[dict, str]:
        parsed_operand = []
        addressing_mode = None

        i = 0
        while i < len(operands):
            operand = operands[i]

            if operand == '[': # Indirect memory addressing
                if operands[i+2] == ']':
                    value, addressing_mode = self.parse_operands([operands[i+1]])
                    parsed_operand.append({"type": "indirect", "value": value[0]})
                    addressing_mode = "indirect_reg" if addressing_mode == "reg" else "indirect_imm16"
                    i += 2
                elif operands[i+2] in ['+', '-'] and operands[i+4] == ']':
                    a, _ = self.parse_operands([operands[i+1]])
                    b, _ = self.parse_operands([operands[i+3]])
                    if a[0]["type"] == b[0]["type"]:
                        raise SyntaxError(f"Indirect offset addressing must use a register and an immediate (line {self.line_num[self.filename[-1]]})")
                    parsed_operand.append({"type": "indirect_offset", "value": {
                        # TODO: apply sign to b value (negative only possible for immediates as b)
                        # "offset_sign": operands[i+2], # TODO: can registers even have negative offset? It seems like would need an extra bit/addressing mode
                        "reg": a[0] if a[0]["type"] == "register" else b[0],
                        "imm16": b[0] if b[0]["type"] == "number" else a[0]
                    }})
                    addressing_mode = "indirect_offset"
                    i += 4
                else:
                    raise SyntaxError(f"Invalid indirect offset addressing (line {self.line_num[self.filename[-1]]})")
            elif operand in REGISTERS:
                value = REGISTERS[operand]
                parsed_operand.append({"type": "register", "value": value})
                addressing_mode = "reg"
            elif operand.startswith('.'):
                value = f"{self.current_scope}{operand}"
                parsed_operand.append({"type": "symbol_ref", "value": value})
                addressing_mode = "imm16"
            elif operand.startswith(("'", '"')) & operand.endswith(("'", '"')):
                value = self.parse_string(operand)[0]
                parsed_operand.append({"type": "number", "value": value})
                addressing_mode = self.infer_imm_mode(value)
            elif operand.startswith("0x"):
                value = int(operand, 16)
                parsed_operand.append({"type": "number", "value": value})
                addressing_mode = self.infer_imm_mode(value)
            elif operand.startswith("0b"):
                value = int(operand, 2)
                parsed_operand.append({"type": "number", "value": value})
                addressing_mode = self.infer_imm_mode(value)
            elif operand.isdigit():
                value = int(operand)
                parsed_operand.append({"type": "number", "value": value})
                addressing_mode = self.infer_imm_mode(value)
            elif operand in self.assembler.symbols:
                operand, addressing_mode = self.parse_operands([self.assembler.symbols[operand]])
                parsed_operand.extend(operand)
            elif operand[0].isalpha():
                parsed_operand.append({"type": "symbol_ref", "value": operand})
                addressing_mode = "imm16"
            else:
                raise SyntaxError(f"Invalid operand '{operand}' (line {self.line_num[self.filename[-1]]})")
            i += 1

        return parsed_operand, addressing_mode

    def get_instruction_length(self, instruction: dict) -> int:
        instruction_length = 2 # Default size of all instruction (in bytes)

        if "operands" not in instruction: # If an instruction doesn't have operands, it's always 2 bytes long
            return instruction_length
        elif instruction["addressing_mode"] in ["imm8"]:
            instruction_length += 1
        elif instruction["addressing_mode"] in ["imm16", "indirect_offset", "indirect_imm16"]:
            instruction_length += 2

        return instruction_length

    def parse_directive(self, tokens: List[str]):
        directive = tokens[0].lstrip('@')
        if directive == "let":
            name, _, value = tokens[1:]
            self.check_symbol_name(name)
            self.assembler.symbols[name] = value
        elif directive == "data":
            data = self.encode_data(tokens[1:])
            self.assembler.program.append({"type": "data", "value": {
                "data": data, "address": self.pc, "length": len(data)
            }})
            self.pc += len(data)
        elif directive == "import":
            filename = tokens[1].strip("\"\'")
            if not filename[0].isalpha():
                raise SyntaxError(f"Invalid filename {filename} (line {self.line_num[self.filename[-1]]})")
            self.imports.append(filename)

        else:
            raise SyntaxError(f"Unknown directive '@{directive}' (line {self.line_num[self.filename[-1]]})")

    def parse_label(self, tokens: List[str]):
        label = tokens[0].rstrip(':')
        if label.startswith('.'):
            if self.current_scope is None:
                raise SyntaxError(f"Local label '{label}' must follow a global label (line {self.line_num[self.filename[-1]]})")
            full_label = f"{self.current_scope}{label}"
        else:
            self.current_scope = label
            full_label = label

        self.check_symbol_name(full_label)
        self.assembler.symbols[full_label] = self.pc

        if len(tokens) > 1: # Parse other code/directives on the same line
            return self.parse_line(' '.join(tokens[1:]))

    def parse_string(self, string: str) -> bytes:
        string = string[1:-1] # Strip quote marks
        for esc, real in { r"\n": "\n", r"\t": "\t", r"\0": "\x00", r"\\": "\\", r"\'": "'",  r"\"": '"', }.items():
            string = string.replace(esc, real) # Decode escape sequences like \n, \t, \0, \\ etc.
        return string.encode(self.assembler.charset) # Encode string to selected character set (e.g. 'µ' -> 0xE6 for CP437)

    def encode_data(self, tokens: List[str]) -> bytearray:
        data = bytearray()
        for token in tokens:
            if token.startswith(("'", '"')) and token.endswith(("'", '"')):
                data.extend(self.parse_string(token))
            elif token.startswith("0x"):
                data.append(int(token, 16)) #TODO: use to_bytes with a heper function that calculates the size
            elif token.startswith("0b"):
                data.append(int(token, 2))
            elif token.isdigit():
                data.append(int(token))
            else:
                raise AssemblerError(f"Invalid data literal '{token}'")
        return data

    def infer_imm_mode(self, value: int) -> str:
        return "imm16" if value > 0xFF else "imm8" if value > 0xF else "imm4"

    def check_symbol_name(self, name):
        if name.lower() in REGISTERS:
            raise AssemblerError(f"Reserved symbol name '{name}'")