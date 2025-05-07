import argparse
import re
from typing import Optional
import codecs


#    NOP         No opperation
#    HLT         Halt
#    LDI         Load immediate value into register
#    LD          Load from 14 bit address into register
#    LDIR        Load from address stored in source register into destination register
#    LDIRP       Load from address stored in register pair into destination register
#    ST          Store to 14 bit address from register
#    STIR        Store value in register to location in source register
#    STIRP       Store value in register into location in register pair
#    MOV         Move from source to destination register
#    ADD         Add from 2 source registers to destination register
#    ADC         Add with carry
#    ADDI        Add source register with 8 bit immediate value into source register
#    ADDIW       Add register pair with 16 bit immediate value into source register pair
#    AND         And 2 source registers into destination register
#    OR          Or 2 source registers into destination register
#    XOR         Xor 2 source registers into destination register
#    NOT         Not source register into destination register
#    OUT         Output 8 bit value
#    OUTP        Output 16 bit value
#    OUTA        Output Ascii value
#    CPI         Compare source register to 8 bit immediate value
#    JMP         Unconditional jump to memory address register
#    BGT         Branch if N flag not set to memory address register
#    BLT         Branch if N flag set to memory address register
#    BEQ         Branch if Z flag set to memory address register
#    CALL        Branch to memory address register and push program counter to the stack
#    RET         Return from function poped from stack


class AssemblyParser:

    #Constructor initializes bytarray, adresses and lable identifiers
    def __init__(self):
        self.output = bytearray(0x10000)
        self.current_input = ""
        self.current_addr = 0
        self.mem_addr = 0x8000
        self.labels = {}
        self.unresolved = []

    #Open file and parse each part
    def parse_file(self, file: str, outFile: str):
        with open(file, "r") as i:
            self.current_input = i.read()
        self.parse_program()
        self.resolve_labels()
        self.current_input = None
        with open(outFile,"wb") as f:
            f.write(self.output)
        print(f"Wrote {len(self.output)} bytes to {outFile}")

    #While there is an input parse individual instruction
    def parse_program(self):
        while len(self.current_input) > 0:
            self.parse_instruction()

    #Skip over whitespace, and comments        
    def skip(self):
        while True:
            if m := self.consume_regex(r'\s+'):
                continue
            if m := self.consume_regex(r'(#|//).*[\n$]'):
                continue
            if m := self.consume_regex(r'(?s)/\*.*\*/'):
                continue
            break
    
    #Return regular expression
    def consume_regex(self, regex) -> Optional[re.Match]:
        if m := re.match(regex,self.current_input):
            self.current_input = self.current_input[len(m[0]):]
            return m
        return None
    
    #Parse out individual instruction
    def parse_instruction(self):
        self.skip()
        
        #Identify labels
        if m:= self.consume_regex(r'([A-Za-z_]\w*):'):
            label = m.group(1)
            self.labels[label] = self.current_addr
            print(f"Label {label} defined at address {self.current_addr}")
            return 
        
        #Encode ascii values at index
        if m := self.consume_regex(r'\.ascii\s+"((?:[^"\\]|\\.)*)"'):
            s = bytes(m.group(1), "utf-8").decode("unicode_escape") 
            data = s.encode('ascii')
            for i in data:
                self.output[self.mem_addr] += i
                self.mem_addr += 1
            print(f'.ascii "{s}" → {list(data)}')
            return
        
        #LDI Rd, 0xImm
        if m := self.consume_regex(r'LDI\s+[R](\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)'):
            reg = int(m.group(1))
            imm_str = m.group(2)
            imm = int(imm_str,0)
            op = 0x020000
            op |= ((reg & 0x03) << 8)
            op |= (imm & 0xFF)
            op &= 0xFFFFFF
            code = op.to_bytes(3,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #LD Rd, 0xAddress
        if m := self.consume_regex(r'LD\s+[R](\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*'):
            reg = int(m.group(1))
            addr_str = m.group(2)
            addr = int(addr_str,0)
            addr &= 0x3FFF
            op = 0x030000
            op |= ((reg & 0x03) << 14)
            op |= addr
            op &= 0xFFFFFF
            code = op.to_bytes(3,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #St Rx, 0xAddress
        if m := self.consume_regex(r'ST\s+[R](\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*'):
            reg = int(m.group(1))
            addr_str = m.group(2)
            addr = int(addr_str,0)
            addr &= 0x3FFF
            op = 0x040000
            op |= ((reg & 0x03) << 14)
            op |= addr
            op &= 0xFFFFFF
            code = op.to_bytes(3,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #ADD Rd, Rx, Ry
        if m := self.consume_regex(r'ADD\s+R(\d+)\s*,\s*R(\d+)\s*,\s*R(\d+)'):
            reg1 = int(m.group(1))
            reg2 = int(m.group(2))
            reg3 = int(m.group(3))
            op = 0x0600
            op |= ((reg1 & 0x03 ) << 4) | ((reg2 & 0x03) << 2) | (reg3 & 0x03)
            op &= 0xFFFF
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #ADC Rd, Rx, Ry
        if m := self.consume_regex(r'ADC\s+R(\d+)\s*,\s*R(\d+)\s*,\s*R(\d+)'):
            reg1 = int(m.group(1))
            reg2 = int(m.group(2))
            reg3 = int(m.group(3))
            op = 0x0700
            op |= ((reg1 & 0x03 ) << 4) | ((reg2 & 0x03) << 2) | (reg3 & 0x03)
            op &= 0xFFFF
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #OUT Rx
        if m := self.consume_regex(r'OUT\s+R(\d+)'):
            reg = int(m.group(1))
            op = 0x0A00
            op |= (reg & 0x03)
            op &= (op & 0xFFFF)
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #CPI Rx, 0xImm
        if m := self.consume_regex(r'CPI\s+[R](\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)'):
            reg = int(m.group(1))
            imm_str = m.group(2)
            imm = int(imm_str,0)
            op = 0x0B0000
            op |= ((reg & 0x03) << 8)
            op |= (imm & 0xFF)
            op &= 0xFFFFFF
            code = op.to_bytes(3,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #BGT MAR
        if m := self.consume_regex(r'BGT\s+([A-Za-z_]\w*)'):
            label = m.group(1)
            op = 0x0D0000 
            self.unresolved.append((label, self.current_addr))
            code = op.to_bytes(3,'big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #BEQ MAR
        if m := self.consume_regex(r'BEQ\s+([A-Za-z_]\w*)'):
            label = m.group(1)
            op = 0x0C0000 
            self.unresolved.append((label, self.current_addr))
            code = op.to_bytes(3,'big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #JMP MAR
        if m := self.consume_regex(r'JMP\s+([A-Za-z_]\w*)'):
            label = m.group(1)
            op = 0x090000 
            self.unresolved.append((label, self.current_addr))
            code = op.to_bytes(3,'big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #MOV Rd, Rx
        if m := self.consume_regex(r'MOV\s+R(\d+)\s*,\s*R(\d+)'):
            reg1 = int(m.group(1))
            reg2 = int(m.group(2))
            op = 0x0500
            op |= ((reg1 & 0x03 ) << 2) | (reg2 & 0x03) 
            op &= 0xFFFF
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #HLT
        if m := self.consume_regex(r'HLT'):
            op = 0x01
            code = op.to_bytes(1,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #NOP
        if m := self.consume_regex(r'NOP'):
            op = 0x00
            code = op.to_bytes(1,byteorder='big')
            self.output += code
            return
        
        #LDIR Rd, (Rx)
        if m := self.consume_regex(r'LDIR\s+R(\d+)\s*,\s*\(R(\d+)\)'):
            rd = int(m.group(1)) & 0x03
            ra = int(m.group(2)) & 0x03
            op = 0x0E0000
            op |= ((ra & 0x03))      
            op |= ((rd & 0x03) << 2) 
            code = op.to_bytes(3, 'big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return

        #STIR (Rx), Ry 
        if m := self.consume_regex(r'STIR\s+\(R(\d+)\)\s*,\s*R(\d+)'):
            ra = int(m.group(1)) & 0x03
            rb = int(m.group(2)) & 0x03
            op = 0x0F0000
            op |= ((ra & 0x03))
            op |= ((rb & 0x03) << 2)
            code = op.to_bytes(3, 'big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return

        #LDIRP Rd, (Rp)
        if m := self.consume_regex(r'LDIRP\s+R(\d+)\s*,\s*\(R(01|23)\)'):
            rd = int(m.group(1)) & 0x03
            pair = 0 if m.group(2) == "01" else 1
            op = 0x1000
            op |= ((rd & 0x03) << 4)
            op |= pair
            code = op.to_bytes(2, 'big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return

        #STIRP (R0), Ry
        if m := self.consume_regex(r'STIRP\s+\(R(01|23)\)\s*,\s*R(\d+)'):
            pair = 0 if m.group(1) == "01" else 1
            rs = int(m.group(2)) & 0x03
            op = 0x1100
            op |= ((rs & 0x03) << 4)
            op |= pair
            code = op.to_bytes(2, 'big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return

        #ADDIW Rp, 0xImm16
        if m := self.consume_regex(r'ADDIW\s+R(01|23)\s*,\s*(0x[0-9A-Fa-f]+|\d+)'):
            pair = 0 if m.group(1) == "01" else 1
            imm = int(m.group(2), 0) & 0xFFFF
            op = 0x12000000
            op |= (pair << 16)
            op |= imm
            code = op.to_bytes(4, 'big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return

        #ADDI Rd, 0xImm8
        if m := self.consume_regex(r'ADDI\s+R(\d+)\s*,\s*(0x[0-9A-Fa-f]+|\d+)'):
            rd = int(m.group(1)) & 0x03
            imm = int(m.group(2), 0) & 0xFF
            op = 0x130000
            op |= (rd << 8) 
            op |= imm
            code = op.to_bytes(3, byteorder='big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return

        #OUTP Rp
        if m := self.consume_regex(r'OUTP\s+R(01|23)'):
            pair = 0 if m.group(1) == "01" else 1
            op = 0x1400 | pair
            code = op.to_bytes(2, 'big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return

        #OUTA Rx
        if m := self.consume_regex(r'OUTA\s+R(\d+)'):
            ra = int(m.group(1)) & 0x03
            op = 0x1500 | ra
            code = op.to_bytes(2, 'big')
            for i in code:
                self.output[self.current_addr] = i
                self.current_addr += 1
            return
        
        #AND Rd, Rx, Ry
        if m := self.consume_regex(r'AND\s+R(\d+)\s*,\s*R(\d+)\s*,\s*R(\d+)'):
            reg1 = int(m.group(1))
            reg2 = int(m.group(2))
            reg3 = int(m.group(3))
            op = 0x0800
            op |= ((reg1 & 0x03 ) << 4) | ((reg2 & 0x03) << 2) | (reg3 & 0x03)
            op &= 0xFFFF
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #OR Rd, Rx, Ry
        if m := self.consume_regex(r'OR\s+R(\d+)\s*,\s*R(\d+)\s*,\s*R(\d+)'):
            reg1 = int(m.group(1))
            reg2 = int(m.group(2))
            reg3 = int(m.group(3))
            op = 0x1600
            op |= ((reg1 & 0x03 ) << 4) | ((reg2 & 0x03) << 2) | (reg3 & 0x03)
            op &= 0xFFFF
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #XOR Rd, Rx, Ry
        if m := self.consume_regex(r'XOR\s+R(\d+)\s*,\s*R(\d+)\s*,\s*R(\d+)'):
            reg1 = int(m.group(1))
            reg2 = int(m.group(2))
            reg3 = int(m.group(3))
            op = 0x1800
            op |= ((reg1 & 0x03 ) << 4) | ((reg2 & 0x03) << 2) | (reg3 & 0x03)
            op &= 0xFFFF
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #Not Rd, Rx
        if m := self.consume_regex(r'NOT\s+R(\d+)\s*,\s*R(\d+)'):
            reg1 = int(m.group(1))
            reg2 = int(m.group(2))
            op = 0x1700
            op |= ((reg1 & 0x03 ) << 4) | ((reg2 & 0x03) << 2)
            op &= 0xFFFF
            code = op.to_bytes(2,byteorder='big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #BLT MAR
        if m := self.consume_regex(r'BLT\s+([A-Za-z_]\w*)'):
            label = m.group(1)
            op = 0x190000 
            self.unresolved.append((label, self.current_addr))
            code = op.to_bytes(3,'big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #CALL MAR
        if m := self.consume_regex(r'CALL\s+([A-Za-z_]\w*)'):
            label = m.group(1)
            op = 0x200000  
            self.unresolved.append((label, self.current_addr))
            code = op.to_bytes(3,'big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #RET
        if m := self.consume_regex(r'RET'):
            op = 0x21
            code = op.to_bytes(1,'big')
            for i in code:
                self.output[self.current_addr] += i
                self.current_addr += 1
            return
        
        #Unknown token
        unknown = self.consume_regex(r'\S+')
        if unknown:
            print(f"Unknown token: {unknown.group(0)}")
        
    #Look for labels and add index at output    
    def resolve_labels(self):
        for label, offset in self.unresolved:
            if label not in self.labels:
                raise SyntaxError(f"Undefined label: {label}")
            addr = self.labels[label]
            print(f"Resolving BR to '{label}' at offset {offset} → {addr:#04x}")
            self.output[offset + 1] = (addr >> 8) & 0xFF
            self.output[offset + 2] = addr & 0xFF

#Take in arguments from command line
parser = argparse.ArgumentParser()
parser.add_argument("inputs",metavar="INPUT",nargs="*",help="input files to assemble")
parser.add_argument("-o", "--output", default="out.bin", help="output binary file")
args = parser.parse_args()

#Parse file
parser = AssemblyParser()
for i in args.inputs:
    parser.parse_file(i,args.output)