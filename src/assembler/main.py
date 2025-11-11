from assembler import Assembler
import argparse

def hexdump(data, start=0, end=None):
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
    parser.add_argument("-e", "--endianess", choices=["little", "big"], default="big", help="byteorder to use for encoding bytes")
    args = parser.parse_args()
    assembler = Assembler(charset=args.charset, endianess=args.endianess)

    with open(args.filename, "r") as input_file:
        program = input_file.read().splitlines()
        output = assembler.assemble(program, args.filename)
        print(f"Assembled \"{args.filename}\" into {len(output)} bytes.")
        if args.output:
            with open(args.output, "wb") as output_file:
                output_file.write(output)
        else: # If no output file specified, print output as a hexdump
            hexdump(output)