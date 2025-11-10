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
    def __init__(self, charset):
        self.charset = charset
        self.parsed_program = []
        self.symbols = {}
        self.pc = 0
        self.line = 1
        self.current_scope = None # Current global scope defined by the last global label

    # Takes in an instruction as a list of tokens, parses the tokens, calcuates the instruction size based on the addressing mode, etc.
    def parse_instruction(self, tokens):
        mnemonic = tokens[0].upper()
        opcode = OPCODES.get(mnemonic)
        if opcode == None:
            raise ValueError(f"Unknown instruction: {mnemonic}")
        instruction = {"mnemonic": mnemonic, "opcode": opcode, "address": self.pc}
        operands = tokens[1:]
        if operands:
            instruction["operands"], instruction["addressing_mode"] = self.parse_operands(operands)
        instruction["length"] = self.get_instruction_length(instruction)
        self.pc += instruction["length"]
        self.parsed_program.append({"type": "instruction", "value": instruction})

    def parse_operands(self, operands,):
        parsed = []
        i = 0
        addressing_mode = None

        while i < len(operands):
            operand = operands[i]

            if operand == '[': # Indirect addressing
                if operands[i+2] == ']':
                    # TODO: indirect_imm16 seems to not work
                    operand, addressing_mode = self.parse_operands([operands[i+1]])
                    parsed.append({"type": "indirect", "value": operand[0]})
                    addressing_mode = "indirect_reg" if addressing_mode == "reg" else "indirect_imm16"
                    i += 2
                elif (operands[i+2] == '+' or operands[i+2] == '-') and operands[i+4] == ']':
                    operand = {"offset_sign": operands[i+2]}
                    a, _ = self.parse_operands([operands[i+1]])
                    b, _ = self.parse_operands([operands[i+3]])
                    operand["reg"] = a[0] if a[0]["type"] == "register" else b[0]
                    operand["imm16"] = a[0] if a[0]["type"] == "number" else b[0]
                    # if operand["a"]["type"] == "register" and operand["b"]["type"] == "register":
                        # raise ValueError(f"Indirect offset addressing can only use one register. Other value must be immediate")
                    parsed.append({"type": "indirect_offset", "value": operand})
                    addressing_mode =  "indirect_reg_offset"
                    i += 4
            elif isinstance(operand, int): # Already parsed into a number
                parsed.append({"type": "number", "value": operand})
            elif operand in REGISTERS:
                parsed.append({"type": "register", "value": REGISTERS[operand]})
                addressing_mode = "reg"
            elif operand.startswith('.'): # Append current scope if the operand is a local label reference
                parsed.append({"type": "symbol_ref", "value": f"{self.current_scope}{operand}"})
                addressing_mode = "imm16"
            elif operand.startswith('\''): # Turn character into it's CP437 ASCII value #TODO: this could also be two characters for a 16-bit value
                parsed.append({"type": "number", "value": self.parse_string(operand)[0]})
            elif operand.startswith("0x"):
                value = int(operand, 16)
                parsed.append({"type": "number", "value": value})
                addressing_mode = "imm16" if value > 0xFF else "imm8" if value > 0xF else "imm4"
            elif operand.startswith("0b"):
                value = int(operand, 2)
                parsed.append({"type": "number", "value": value})
                addressing_mode = "imm16" if value > 0xFF else "imm8" if value > 0xF else "imm4"
            elif operand.isdigit(): #TODO: negative numbers
                value = int(operand, 10)
                parsed.append({"type": "number", "value": value})
                addressing_mode = "imm16" if value > 0xFF else "imm8" if value > 0xF else "imm4"
            elif operand in self.symbols: # If it's a symbol, replace it with it's value and parse the new value
                operand, addressing_mode = self.parse_operands([self.symbols[operand]])
                parsed.extend(operand)
            elif operand[0].isalpha(): # If first character is either A-Z or a-z, assume it's a symbol reference
                parsed.append({"type": "symbol_ref", "value": operand})
                addressing_mode = "imm16"
            else:
                raise ValueError(f"Unable to parse operand: {operand}")

            i += 1

        return parsed, addressing_mode

    def parse_string(self, string):
        string = string.strip('\"').strip('\'') # Strip quote marks #TODO: also strips them from stuff like this "\'test\'" -> \test\
        # Decode escape sequences like \n, \t, \0, \\ etc.
        escape_map = { r"\n": "\n", r"\t": "\t", r"\0": "\x00", r"\\": "\\", r"\'": "'",  r"\"": '"', }
        for esc, real in escape_map.items():
            string = string.replace(esc, real)
        return string.encode(self.charset) # Encode string to selected character set (e.g. 'µ' -> 0xE6 for CP437)

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

        # Handle code/data on same line, e.g. str: @data "Hello World!\0"
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
                assembler.assemble(program) # TODO: Need to merge symbol table & entries with the current one and then assemble them together
        elif directive == "data":
            encoded_data = self.encode_data(tokens[1:])
            data = {"data": encoded_data, "address": self.pc, "length": len(encoded_data)}
            self.pc += data["length"]
            self.parsed_program.append({"type": "data", "value": data})

    def check_symbol_name(self, name):
        RESERVED_SYMBOL_NAMES = []
        if name in RESERVED_SYMBOL_NAMES or name.lower() in REGISTERS.keys():
            raise ValueError(f"Used reserved symbol name: {name}")

    def encode_data(self, tokens):
        result = bytearray()
        for data in tokens:
            if data.startswith('"') or data.startswith("'"):
                result.extend(self.parse_string(data))
            elif data.startswith("0x"):
                result.append(int(data, 16) & 0xFF)
            elif data.isdigit():
                result.append(int(data) & 0xFF)
            else:
                raise ValueError(f"Unsupported data format: {data}")
        return result

    def parse_tokens(self, tokens):
        if tokens[0].startswith('@'):
            self.parse_directive(tokens)
        elif tokens[0].endswith(':'):
            self.parse_label(tokens)
        else:
            self.parse_instruction(tokens)

    def resolve_symbols(self):
        for entry in self.parsed_program:
            if entry["type"] == "data": # Skip non-instructions
                continue
            instruction_entry = entry["value"]
            if not "operands" in instruction_entry: # Skip instructions with no operands
                continue
            operands = instruction_entry["operands"]
            addressing_mode = instruction_entry["addressing_mode"]

            if addressing_mode == "imm16" and operands[0]["type"] == "symbol_ref":
                operands[0]["type"] = "number"
                operands[0]["value"] = self.symbols[operands[0]["value"]]

    def encode_program(self):
        output = bytearray()
        for entry in self.parsed_program:
            if entry["value"]["address"] != len(output):
                raise Exception(f"Mismatch between expected address for emitted bytes and actual address")
            if entry["type"] == "data":
                data_entry = entry["value"]
                output.extend(data_entry["data"])
            elif entry["type"] == "instruction":
                instruction_entry = entry["value"]
                instruction = instruction_entry["opcode"] << 10
                imm8 = None
                imm16 = None

                if "operands" in instruction_entry:
                    mnemonic = instruction_entry["mnemonic"]
                    operands = instruction_entry["operands"]
                    addressing_mode = instruction_entry["addressing_mode"]

                    if addressing_mode == "imm4": #TODO: set correct addr mode & imm4 value for inc/dec
                        instruction |= operands[0]["value"] << 7 # Register
                        instruction |= operands[1]["value"] << 3 # Imm4
                        instruction |= 0b000 # Addressing mode
                    elif addressing_mode == "imm8":
                        instruction |= operands[0]["value"] << 7 # Register
                        imm8 = operands[1]["value"] # Imm8
                        instruction |= 0b001 # Addressing mode
                    elif addressing_mode == "imm16":
                        if mnemonic in ["MOV", "STOREB", "STORE"]:
                            instruction |= operands[0]["value"] << 7 # Register
                            imm16 = operands[1]["value"] # Imm16
                        else:
                            imm16 = operands[0]["value"] # Imm16
                        instruction |= 0b010 # Addressing mode
                    elif addressing_mode == "reg":
                        offset = 3 if mnemonic in ["PUSHB", "PUSH"] else 7 # Push instructions use 4-bit field for their source register
                        instruction |= operands[0]["value"] << offset # Register
                        instruction |= 0b011 # Addressing mode
                    elif addressing_mode == "indirect_reg":
                        instruction |= operands[0]["value"] << 7 # Register
                        instruction |= operands[1]["value"]["value"] << 3 # Indirect address register
                        instruction |= 0b100 # Addressing mode
                    elif addressing_mode == "indirect_reg_offset": # TODO: handle signed values
                        instruction |= operands[0]["value"] << 7 # Register
                        offset = operands[1]["value"]
                        instruction |= offset["reg"]["value"] << 3 # Indirect offset register
                        imm16 = offset["imm16"]["value"] # Indirect offset imm16
                        instruction |= 0b101 # Addressing mode
                    elif addressing_mode == "indirect_imm16":
                        instruction |= operands[0]["value"] << 7 # Register
                        imm16 = operands[1]["value"]["value"] # Indirect address imm16

                output.append((instruction >> 8) & 0xFF)
                output.append(instruction & 0xFF)
                if imm8 != None:
                    output.append(imm8)
                elif imm16 != None:
                    output.append((imm16 >> 8) & 0xFF)
                    output.append(imm16 & 0xFF)

        return output

    def assemble(self, program):
        for line in program:
            line = line.split(';')[0].strip() # Strip comments & whitespace
            if not line:
                continue # Skip empty lines
            tokens = re.findall(r'\[|\]|"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|[^\s,\[\]]+', line) # Split into tokens through one or more commas ',' or whitespaces '\s'
            self.parse_tokens(tokens)
            self.line += 1
        self.resolve_symbols()
        return self.encode_program()

def dump(data, start=0, end=None):
    if end is None:
        end = len(data)
    for addr in range(start, end, 16):
        chunk = data[addr:addr+16]
        hex_bytes = ' '.join(f'{b:02X}' for b in chunk)
        ascii_repr = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{addr:04X}: {hex_bytes:<48} {ascii_repr}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="YR-µ16 Assembler")
    parser.add_argument("filename", help="source code file to assemble")
    parser.add_argument("-o", "--output", help="output file for the assembled program")
    parser.add_argument("-c", "--charset", choices=["cp437", "cp850"], default="cp437", help="charset to use for encoding chars/strings")
    args = parser.parse_args()
    assembler = Assembler(charset=args.charset)

    with open(args.filename, "r") as input_file:
        program = input_file.read().splitlines()
        output = assembler.assemble(program)
        print(f"Assembled \"{args.filename}\" into {len(output)} bytes.")
        if args.output:
            with open(args.output, "wb") as output_file:
                output_file.write(output)
        else: # If no output file specified, print output as a hexdump
            dump(output)