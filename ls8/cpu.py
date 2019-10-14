"""CPU functionality."""

import sys
from instructions import *

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0
        self.running = True
        self.instructions = {}
        self.instructions[HLT] = self.halt
        self.instructions[LDI] = self.ldi
        self.instructions[PRN] = self.prn

        self.alu_ops = {}
        self.alu_ops[MUL] = "MUL"


    def parse(self, instruction):
        return instruction.split('#')[0]

    def load(self, file):
        """Load a program into memory."""

        address = 0

        # load program by reading the file
        # NOTE: we expect the file to be valid and exist, thanks to ls8
        # TODO: This parser can be cleaned up with more consistent return
        #   handling blank lines inside of the parsed method
        with open(file) as program:
            instruction = program.readline()
            while instruction:
                parsed = self.parse(instruction.strip())
                if parsed:
                    self.ram[address] = int(parsed, 2)
                    address += 1
                instruction = program.readline()

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")
    
    def ldi(self, mar, mdr):
        if mar <= 4:
            self.reg[mar] = mdr
        else:
            raise OverflowError('Cannot overwrite reserved registers.')
    
    def prn(self, mar):
        print(self.reg[mar])

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()
    
    def ram_read(self, mar):
        # access self.RAM[MAR]
        return self.ram[mar]

    def ram_write(self, mdr, mar):
        self.ram[mar] = mdr

    def halt(self):
        self.running = False

    def execute(self, ir, op_a, op_b):
        operands = ir >> 6
        if operands == 0:
            self.instructions[ir]()
        elif operands == 1:
            self.instructions[ir](op_a)
        elif operands == 2:
            self.instructions[ir](op_a, op_b)
        else:
            raise EnvironmentError('Too many operands provided, please use one or two.')

    def run(self):
        """Run the CPU."""
        while self.running:
            ir = self.ram_read(self.pc)

            # TODO: Handle overflow here ?
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            if ir in self.instructions:
                self.execute(ir, operand_a, operand_b)
            elif (ir >> 5 & 1) == 1 and ir in self.alu_ops:
                self.alu(self.alu_ops[ir], operand_a, operand_b)
            else:
                print('unknown command provided')
                # raise NotImplementedError("Unknown command provided.")
            
            self.pc += (ir >> 6) + 1


