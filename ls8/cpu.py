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

        # Reserved Registers
        self.reg[7] = 0xF4  # if 0xF3 == 0 else 0xF3 # Stack Pointer

        # PC Instructions
        self.instructions = {}
        self.instructions[HLT] = self.halt
        self.instructions[LDI] = self.ldi
        self.instructions[PRN] = self.prn
        self.instructions[POP] = self.pop
        self.instructions[PUSH] = self.push
        self.instructions[CALL] = self.call
        self.instructions[RET] = self.ret
        self.instructions[ST] = self.st

        # ALU OPERATIONS
        self.alu_ops = {}
        self.alu_ops[MUL] = "MUL"
        self.alu_ops[ADD] = "ADD"

        # Possibly Temp
        self.cont = False

    def get_sp(self):
        return self.reg[7]
    
    def set_sp(self, mdr):
        self.reg[7] = mdr

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
            # self.reg[reg_a] = self.reg[reg_a] & 0xFF  # out of range error?
        else:
            raise Exception("Unsupported ALU operation")
    
    def ldi(self, mar, mdr, internal=False):
        # if mar <= 4:
        #     self.reg[mar] = mdr
        # elif internal == True and mar <= 7:
        #     self.reg[mar] = mdr
        # else:
        #     raise OverflowError('Cannot overwrite reserved registers.')
        self.reg[mar] = mdr
    
    def pop(self, mar, internal=False):
        sp = self.get_sp()
        self.ldi(mar, self.ram[sp], internal)
        self.set_sp(sp + 1)

    def push(self, mar):
        sp = self.get_sp()
        self.set_sp(sp - 1)
        self.ram[sp - 1] = self.reg[mar]

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
    
    def call(self, mar):
        # push address after call to stack
        # TODO: Update this so it's not a manual push
        sp = self.get_sp()
        self.set_sp(sp - 1)
        self.ram[sp - 1] = self.pc + 2
        # set the PC to the correct address
        self.pc = self.reg[mar]
        self.cont = True

    def ret(self):
        # Pop the value from the top of the stack and store it in the PC
        # Manual pop for now, TODO: Update this so it is not a manual pop
        sp = self.get_sp()
        self.pc = self.ram_read(sp)
        self.set_sp(sp + 1)
        
        self.cont = True
    
    def ram_read(self, mar):
        # access self.RAM[MAR]
        return self.ram[mar]

    def ram_write(self, mdr, mar):
        self.ram[mar] = mdr

    def halt(self):
        self.running = False
    
    def st(self, reg_a, reg_b):
        # Take value (MDR) in reg_b and store it in address (MAR) in reg_a
        mdr = self.reg[reg_b]
        mar = self.reg[reg_a]
        self.ram[mar] = mdr

    def execute(self, ir, op_a, op_b):
        operands = ir >> 6
        if operands == 0:
            self.instructions[ir]()
        elif operands == 1:
            self.instructions[ir](op_a)
        elif operands == 2:
            self.instructions[ir](op_a, op_b)
        else:
            raise Exception('Too many operands provided, please use one or two.')

    def run(self):
        """Run the CPU."""
        while self.running:
            ir = self.ram_read(self.pc)
            self.trace()

            # TODO: Handle overflow here ?
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            if ir in self.instructions:
                self.execute(ir, operand_a, operand_b)
            elif (ir >> 5 & 1) == 1 and ir in self.alu_ops:
                self.alu(self.alu_ops[ir], operand_a, operand_b)
            else:
                # print('unknown command provided', bin(ir))
                raise NotImplementedError(f'Unknown command {bin(ir)} provided.')
            
            if self.cont:
                self.cont = False
                continue
            
            self.pc += (ir >> 6) + 1


