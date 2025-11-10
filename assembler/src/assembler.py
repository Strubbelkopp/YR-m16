import argparse
import re

REGISTERS = {
    "r0": 0, "r1": 1, "r2": 2, "r3": 3,
    "r4": 4, "r5": 5, "r6": 6, "r7": 7,
    "sp": 7, "pc": 8
}

OPCODES = {
    "NOP":      0b00_0000, "HALT":      0b00_0001,
    "RET":      0b00_0010, "MOV":       0b00_0011,
    "ADD":      0b01_0000, "INC":       0b01_0000,
    "SUB":      0b01_0001, "DEC":       0b01_0001,
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

class Assembler():
    def __init__(self):
        self.instructions = []
        self.symbols = {}
        self.pc = 0
        self.line = 1
        self.current_scope = None # Current global scope defined by the last global label
        self.output = bytearray()

    # Takes in an instruction as a list of tokens, parses the tokens, calcuates the instruction size based on the addressing mode, etc.
    def parse_instruction(self, tokens):
        mnemonic = tokens[0].upper()
        opcode = OPCODES.get(mnemonic)
        if opcode == None:
            raise ValueError(f"Unknown instruction: {mnemonic}")
        instruction = {"mnemonic": mnemonic, "opcode": opcode, "address": self.pc}

        operands = tokens[1:]
        if operands:
            instruction["operands"] = self.parse_operands(operands)

        instruction["length"] = self.get_instruction_length(instruction)
        self.pc += instruction["length"]
        self.instructions.append({"type": "instruction", "value": instruction})
        print({"type": "instruction", "value": instruction})

    def parse_operands(self, operands):
        parsed = []
        i = 0

        while i < len(operands):
            operand = operands[i]

            if operand == '[': # Indirect addressing
                if operands[i+2] == ']':
                    operand = self.parse_operands([operands[i+1]])
                    parsed.append({"type": "indirect", "value": operand[0]})
                    i += 2
                elif (operands[i+2] == '+' or operands[i+2] == '-') and operands[i+4] == ']':
                    operand = {"offset_sign": operands[i+2]}
                    operand["a"] = self.parse_operands([operands[i+1]])[0]
                    operand["b"] = self.parse_operands([operands[i+3]])[0]
                    if operand["a"]["type"] == "register" and operand["b"]["type"] == "register":
                        raise ValueError(f"Indirect offset addressing can only use one register. Other value must be immediate")
                    parsed.append({"type": "indirect_offset", "value": operand})
                    i += 4
            elif isinstance(operand, int): # Already parsed into a number
                parsed.append({"type": "number", "value": operand})
            elif operand in REGISTERS:
                parsed.append({"type": "register", "value": REGISTERS[operand]})
            elif operand.startswith('.'): # Append current scope if the operand is a local label reference
                parsed.append({"type": "symbol_ref", "value": f"{self.current_scope}{operand}"})
            elif operand.startswith('\''): # Turn character into it's CP437 ASCII value #TODO: this could also be two characters for a 16-bit value
                parsed.append({"type": "number", "value": self.parse_string(operand)[0]})
            elif operand.startswith("0x"):
                parsed.append({"type": "number", "value": int(operand, 16)})
            elif operand.startswith("0b"):
                parsed.append({"type": "number", "value": int(operand, 2)})
            elif operand.isdigit(): #TODO: negative numbers
                parsed.append({"type": "number", "value": int(operand, 10)})
            elif operand in self.symbols: # If it's a symbol, replace it with it's value and parse the new value
                parsed.extend(self.parse_operands([self.symbols[operand]]))
            elif operand[0].isalpha(): # If first character is either A-Z or a-z, assume it's a symbol reference
                parsed.append({"type": "symbol_ref", "value": operand})
            else:
                raise ValueError(f"Unable to parse operand: {operand}")

            i += 1

        return parsed

    def parse_string(self, string):
        string = string.strip('\"').strip('\'') # Strip quote marks
        return string.encode("cp437") # Encode string to CP437 character set (e.g. 'µ' -> 0xE6)

    # TODO: instead of this, I could save the addressing mode in the instruction dictionary during operand parsing and just have a simple LUT to check the extra bytes maybe?
    def get_instruction_length(self, instruction):
        instruction_length = 2 # Default size of all instruction (in bytes)

        if "operands" not in instruction: # If an instruction doesn't have operands, it's always 2 bytes long
            return instruction_length
        operands = instruction["operands"]
        opcode = instruction["opcode"]
        if opcode == 0b000011 or (opcode >> 4) == 0b01 or (opcode >> 4) == 0b10: # Instructions that make use of addressing modes
            for operand in operands:
                #TODO: if symbol_ref is a register it would lead to a problem since those don't read any extra bytes. Make sure @let statements MUST come before their references. Even if that were to happen though, it would just leave a 2 byte hole in the code, and since 0 is a NOP instruction, the program would just go on
                if operand["type"] == "number":
                    number = operand["value"]
                    if number > 0xFF: # Imm16
                        instruction_length += 2
                    elif number > 0xF: #Imm8
                        instruction_length += 1
                elif operand["type"] == "indirect" and (operand["value"]["type"] == "number" or operand["value"]["type"] == "symbol_ref"):
                    instruction_length += 2
                elif operand["type"] == "indirect_offset":
                    instruction_length += 2
                elif operand["type"] == "symbol_ref":
                    instruction_length += 2

        return instruction_length

    def parse_label(self, tokens):
        label = tokens[0].rstrip(':')
        if label.startswith('.'):
            if self.current_scope is None:
                raise Exception(f"Local label {label} must have a previous global label, line: {self.line}")
            full_label = f"{self.current_scope}{label}"
        else:
            self.current_scope = label
            full_label = label
        self.check_symbol_name(full_label)
        self.symbols[full_label] = self.pc

        # Handle trailing tokens (code on same line)
        if len(tokens) > 1:
            self.parse_tokens(tokens[1:])

    def parse_directive(self, tokens):
        directive = tokens[0].lstrip('@')
        if directive == "let":
            name, _, value = tokens[1:]
            self.check_symbol_name(name)
            self.symbols[name] = value
        elif directive == "import":
            filename = tokens[1].strip('\"').strip('\'') # Get filename & strip quote marks
            with open(filename, "r") as file:
                program = file.read().splitlines()
                assembler.assemble(program)
        elif directive == "data":
            data = {"data": self.encode_data(tokens[1:])}
            data["length"] = len(data)
            self.pc += data["length"]
            self.instructions.append({"type": "data", "value": data})
            print({"type": "data", "value": data})

    def check_symbol_name(self, name):
        RESERVED_SYMBOL_NAMES = []
        if name in RESERVED_SYMBOL_NAMES or name.lower() in REGISTERS.keys():
            raise ValueError(f"Used reserved symbol name: {name}")

    def encode_data(self, data): #TODO
        return data

    def parse_tokens(self, tokens):
        if tokens[0].startswith('@'):
            self.parse_directive(tokens)
        elif tokens[0].endswith(':'):
            self.parse_label(tokens)
        else:
            self.parse_instruction(tokens)

    def assemble(self, program):
        for line in program:
            line = line.split(';')[0].strip() # Strip comments & whitespace
            if not line:
                continue # Skip empty lines
            tokens = re.findall(r'\[|\]|"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|[^\s,\[\]]+', line) # Split into tokens through one or more commas ',' or whitespaces '\s'
            self.parse_tokens(tokens)
            self.line += 1

        print(self.symbols)
        # print(self.instructions)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="YR-µ16 Assembler")
    parser.add_argument("filename")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    assembler = Assembler()

    with open(args.filename, "r") as file:
        program = file.read().splitlines()
        assembler.assemble(program)

    #TODO: write out as hexdump if -o is not given