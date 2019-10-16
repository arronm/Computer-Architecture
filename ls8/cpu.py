"""CPU functionality."""

import sys
import queue
import threading
import msvcrt
from datetime import datetime, timedelta
from instructions import *

keyQueue = queue.SimpleQueue()
stop_polling = False

class KeyboardPoller(threading.Thread):
  def run(self):
    global stop_polling
    while True:
      keypress = msvcrt.kbhit()
      if keypress:
        key = ord(msvcrt.getch())
        keyQueue.put(key)

      if stop_polling:
        exit()


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0
        self.fl = 0
        self.running = True
        self.interrupt_timer = 1
        self.interrupted = datetime.now()
        self.interrupting = False

        # Reserved Registers
        self.reg[7] = 0xF4 # Stack Pointer

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
        self.instructions[JMP] = self.jmp
        self.instructions[PRA] = self.pra
        self.instructions[IRET] = self.iret

        # ALU OPERATIONS
        self.alu_ops = {}
        self.alu_ops[MUL] = "MUL"
        self.alu_ops[ADD] = "ADD"

        # Possibly Temp
        self.cont = False

    # TODO: Abstract these out into a Register class
    def get_sp(self):
        return self.reg[7]
    
    def set_sp(self, mdr):
        self.reg[7] = mdr

    def get_im(self):
        return self.reg[5]
    
    def set_im(self, mdr):
        self.reg[5] = mdr
    
    def get_is(self):
        return self.reg[6]
    
    def set_is_or(self, mdr):
        self.reg[6] = self.reg[6] | mdr
    
    def set_is(self, mdr):
        self.reg[6] = mdr

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
    
    def jmp(self, reg_a):
        # Jump to the address in reg_a
        self.pc = self.reg[reg_a]
        self.cont = True
    
    def pra(self, reg_a):
        # print alpha (ascii) character stored in reg_a
        print(chr(self.reg[reg_a]))

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
    
    def interrupt(self):
        # if currently processing an interrupt do nothing
        if self.interrupting:
            return

        masked_interrupts = self.get_im() & self.get_is()

        if masked_interrupts == 0:
            return
        

        for i in range(8):
            # Right shift interrupts down by i, then mask with 1 to see if that bit was set
            self.interrupting = ((masked_interrupts >> i) & 1) == 1

            if self.interrupting:
                break
        # set up interrupt status mask
        ism_mask = 1 << i

        # reset the bit with the interrupt status mask
        self.set_is(ism_mask ^ self.get_is())

        # figure out the interrupt vector (address)
        ia = 0xFF - (7 - (i))

        # store current pc value (pc address)
        sp = self.get_sp()
        self.set_sp(sp - 1)
        self.ram[sp - 1] = self.pc

        # store fl value
        sp = self.get_sp()
        self.set_sp(sp - 1)
        self.ram[sp - 1] = self.fl

        # store registers on stack
        for i in range(8):
            self.push(i)
        
        self.pc = self.ram[ia]

    def iret(self):
        for i in range(8):
            self.pop(7 - i)

        self.fl = self.ram[self.get_sp()]
        self.set_sp(self.get_sp() + 1)
        self.pc = self.ram[self.get_sp()]
        self.set_sp(self.get_sp() + 1)
        self.interrupting = False
        self.cont = True

    def run(self):
        """Run the CPU."""
        global stop_polling
        global keyQueue
        poller = KeyboardPoller()
        # poller.start()

        # try:
        while self.running:
            if not keyQueue.empty():
                # characters in key queue, set interrupt
                self.set_is_or(0b00000010) # sets the second bit
                char = keyQueue.get()
                print(chr(char))

            if datetime.now() - self.interrupted >= timedelta(seconds=self.interrupt_timer):
                self.set_is_or(0b000000001)  # sets the first bit
                self.interrupted = datetime.now()

            self.interrupt()

            ir = self.ram_read(self.pc)
            # self.trace()


            # TODO: Handle overflow here ?
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            if ir in self.instructions:
                self.execute(ir, operand_a, operand_b)
            elif (ir >> 5 & 1) == 1 and ir in self.alu_ops:
                self.alu(self.alu_ops[ir], operand_a, operand_b)
            else:
                raise NotImplementedError(f'Unknown command {bin(ir)} provided.')

            if self.cont:
                self.cont = False
                continue
            else:
                self.pc += (ir >> 6) + 1
        # except:
        #     stop_polling = True
        #     print('quitting')
