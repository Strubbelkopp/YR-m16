from typing import Tuple
from parser import Parser, REGISTERS, OPCODES

ADDRESSING_MODES = {
    "imm4": 0b000,          "imm8": 0b001,
    "imm16": 0b010,         "reg": 0b011,
    "indirect_reg": 0b100,  "indirect_offset": 0b101,
    "indirect_imm16": 0b110
}

class Assembler():
    def __init__(self, charset="cp437", endianess="big"):
        self.charset = charset
        self.endianess = endianess
        self.program = []
        self.symbols = {}
        self.parser = Parser(self)

    def assemble(self, program):
        for line in program:
            self.parser.parse_line(line)
            self.parser.line_num += 1
        self.resolve_symbols()
        return self.encode_program()

    def resolve_symbols(self):
        for entry in self.program:
            if entry["type"] != "instruction": # Skip non-instructions
                continue
            instruction = entry["value"]
            if not "operands" in instruction: # Skip instructions with no operands
                continue

            for operand in instruction["operands"]:
                if operand["type"] == "symbol_ref":
                    symbol = operand["value"]
                    if symbol not in self.symbols:
                        raise SyntaxError(f"Unresolved symbol '{symbol}'")
                    operand["type"] = "number"
                    operand["value"] = self.symbols[symbol]

    def encode_program(self):
        output = bytearray()

        for entry in self.program:
            if entry["value"]["address"] != len(output):
                raise Exception(f"Mismatch between expected address for emitted bytes and actual address")
            if entry["type"] == "data":
                output.extend(entry["value"]["data"])
            elif entry["type"] == "instruction":
                # self.print_instruction(entry["value"])
                instruction, imm8, imm16, imm_signed = self.encode_instruction(entry["value"])
                output.extend(instruction.to_bytes(2, self.endianess))
                if imm8 != None:
                    output.append(imm8)
                elif imm16 != None:
                    output.extend(imm16.to_bytes(2, self.endianess, signed=imm_signed))

        return output

    def encode_instruction(self, instruction_entry: dict) -> Tuple[int, int, int, bool]:
        mnemonic = instruction_entry["mnemonic"]
        opcode = OPCODES[mnemonic]
        instruction = opcode << 10
        imm8 = imm16 = None
        imm_signed = False

        if "operands" in instruction_entry:
            operands = instruction_entry["operands"]
            addressing_mode = instruction_entry["addressing_mode"]

            if addressing_mode == "imm4":
                reg, imm4 = self.extract_imm(opcode, operands)
                instruction |= imm4 << 3
                instruction |= reg << 7
                instruction |= ADDRESSING_MODES[addressing_mode]
            elif addressing_mode == "imm8":
                reg, imm8 = self.extract_imm(opcode, operands)
                instruction |= reg << 7
                instruction |= ADDRESSING_MODES[addressing_mode]
            elif addressing_mode == "imm16":
                reg, imm16 = self.extract_imm(opcode, operands)
                instruction |= reg << 7
                instruction |= ADDRESSING_MODES[addressing_mode]
            elif addressing_mode == "reg":
                reg = operands[0]["value"]
                offset = 3 if mnemonic in ["PUSHB", "PUSH"] else 7 # Push instructions use 4-bit field for their source register
                instruction |= reg << offset
                instruction |= ADDRESSING_MODES[addressing_mode]
            elif addressing_mode == "indirect_reg":
                reg = operands[0]["value"]
                address_reg = operands[1]["value"]["value"]
                instruction |= reg << 7
                instruction |= address_reg << 3
                instruction |= ADDRESSING_MODES[addressing_mode]
            elif addressing_mode == "indirect_offset":
                # imm_signed = True
                reg = operands[0]["value"]
                offset = operands[1]["value"]
                offset_reg = offset["reg"]["value"]
                imm16 = offset["imm16"]["value"]
                instruction |= reg << 7
                instruction |= offset_reg << 3
                instruction |= ADDRESSING_MODES[addressing_mode]
            elif addressing_mode == "indirect_imm16":
                reg = operands[0]["value"]
                imm16 = operands[1]["value"]["value"]
                instruction |= reg << 7
                instruction |= ADDRESSING_MODES[addressing_mode]

        return instruction, imm8, imm16, imm_signed

    def extract_imm(self, opcode: int, operands: list) -> Tuple[int, int]:
        if (opcode >> 3) == 0b100 or (opcode >> 1) == 0b10111: # JMP or PUSH instructions have immediate as their only operand
            reg = 0
            imm = operands[0]["value"]
        else:
            reg = operands[0]["value"]
            imm = operands[1]["value"]
        return reg, imm

    def print_instruction(self, instruction: dict):
        if "operands" in instruction:
            print(f"{instruction["mnemonic"]}, {instruction["operands"]}, addr_mod={instruction["addressing_mode"]}")
        else:
            print(f"{instruction["mnemonic"]}")