#!/usr/bin/env python3
# Assembler for mini ARM processor
# 2015-09-09 frederic.boulanger@centralesupelec.fr

import pyparsing as pyp
import sys

symbolicRegisters = {
	'lr': ['r', '7'],
	'sp': ['r', '6']
}

def sym2reg(sym):
	return symbolicRegisters[sym]

def expandSymbolicReg(pstring, loc, toks):
	return [sym2reg(toks[0])]

def expandPush(pstring, loc, toks):
	reg = toks[1]
	exp = [['add', sym2reg('sp'), sym2reg('sp'), ['#', '1']],
	       ['str', reg, [sym2reg('sp')]]]
	return exp

def expandPop(pstring, loc, toks):
	reg = toks[1]
	exp = [['ldr', reg, [sym2reg('sp')]],
	       ['sub', sym2reg('sp'), sym2reg('sp'), ['#', '1']]]
	return exp

def hasStructure(arg):
	return isinstance(arg, (list, tuple, pyp.ParseResults))

def isTag(arg):
	return isinstance(arg, str) and (str.isalpha(arg[0]) or arg[0] == '_')

# pyparsing grammar
# hex value
hexInteger = pyp.Group("0x"+pyp.Regex("[0-9A-F]+"))
# signed integer
integer = pyp.Regex("[+-]?[0-9]+")
# Tags start with a letter or an underscore, and are then composed of letters, digits and underscores
tag = pyp.Word(pyp.alphas+"_", pyp.alphanums+"_")
# int value = signed integer, hex value or tag value
intvalue = integer ^ hexInteger ^ tag
# symbolic name of a register (sp is r6, lr is r7)
symbolicreg = pyp.CaselessLiteral('sp') ^ pyp.CaselessLiteral('lr')
symbolicreg.setParseAction(expandSymbolicReg)
# Registers are noted r0, r1, r2, r3, r4, r5, r6 and r7, or sp (stack pointer, r6) and lr (link register, r7)
register = pyp.Group("r"+pyp.Regex("[0-7]").setName("regnum")) ^ symbolicreg
# An immediate value is an int value prefixed by '#'
immvalue = pyp.Group("#"+intvalue)
# An argument may be a register or an immediate value
argument = register ^ immvalue
# An address may be given as an hex integer or as a symbolic tag
address = tag ^ hexInteger
# A branch address may be a register or an address
braddress = register ^ address
# An indexed address can be an int value or a register and an optional int value between square brackets
# With only an integer, this is direct addressing: ldr r0, 0x1234
# With a register between square brackets, this is direct addressing by register= ldr r0, [r6]
# Only the last case is real indexed addressing: ldr r0, [r6,1]
indexedAddress = intvalue \
               ^ pyp.Group(pyp.Suppress("[")+register+pyp.Suppress(",")+intvalue+pyp.Suppress("]")) \
               ^ pyp.Group(pyp.Suppress("[")+register+pyp.Suppress("]"))
instruction = (pyp.CaselessKeyword("ldr")+register+pyp.Suppress(",")+indexedAddress) \
            ^ (pyp.CaselessKeyword("str")+register+pyp.Suppress(",")+indexedAddress) \
            ^ (pyp.CaselessKeyword("mov")+register+pyp.Suppress(",")+argument) \
            ^ (pyp.CaselessKeyword("add")+register+pyp.Suppress(",")+register+pyp.Suppress(",")+argument) \
            ^ (pyp.CaselessKeyword("sub")+register+pyp.Suppress(",")+register+pyp.Suppress(",")+argument) \
            ^ (pyp.CaselessKeyword("cmp")+register+pyp.Suppress(",")+argument) \
            ^ (pyp.CaselessKeyword("blt")+braddress) \
            ^ (pyp.CaselessKeyword("beq")+braddress) \
            ^ (pyp.CaselessKeyword("b")+braddress) \
            ^ (pyp.CaselessKeyword("bl")+register+pyp.Suppress(",")+braddress).setName('instruction')
smwpseud = pyp.CaselessKeyword("smw")+intvalue
rmwpseud = pyp.CaselessKeyword("rmw")+intvalue
pushpseud = pyp.CaselessKeyword("push")+register
pushpseud.setParseAction(expandPush)
poppseud = pyp.CaselessKeyword("pop")+register
poppseud.setParseAction(expandPop)
pseudoinst = smwpseud \
           ^ rmwpseud \
           ^ pushpseud \
           ^ poppseud
label = pyp.Group("@"+tag)
comment = pyp.Suppress("%")+pyp.Suppress(pyp.restOfLine(""))
codeline = pyp.Group(pyp.Optional(label) + pyp.Group(instruction ^ pseudoinst) + pyp.Optional(comment))
line = (comment ^ codeline)
program = pyp.ZeroOrMore(line)


# opcodes for the instructions
opcodes = {
	'ldr' : 0,	# load register from memory
	'str' : 1,	# store register to memory
	'mov' : 2,	# move register/immediate value to register
	'add' : 3,	# add register and register/immediate value, store result in register
	'sub' : 4,	# subtract register/immediate value from register, store result in register
	'cmp' : 5,	# compare register to register/immediate value, set status register
	'beq' : 6,	# branch if status register Z bit is 1
	'blt' : 7,	# branch if status register N bit is 1
	'b'   : 8,	# branch
	'bl'  : 9,	# branch and link (move pc to lr before branching)
}

# position of the different fields in an instruction word
fieldshifts = {
	'opcode': 12,	# opcode is bits 15-12
	'mode': 11,		# mode is bit 11 (0 = register, 1 = immediate)
	'rx': 8,		# rx register number is bits 10-8
	'ry': 5,		# ry register number is bits 7-5
	'rz': 2			# rz register number is bits 4-2
}

# Map from labels to addresses
labels = {}
# Current program counter
pc = 0

# During first pas, do not check labels
firstPass = True

# Get an integer value from an intvalue ParseResult
def getIntValue(value):
	if hasStructure(value):  # ParseResult ['0x', hexvalue], unsigned hex value
		val = int(value[1], 16)
		if val >= (1 << 16):
			print('# Error: value ' + value[1] + ' does not fit into 16 bits')
		return val % (1 << 16)
	elif isTag(value):       # tag
		return getLabelValue(value)
	else:				     # simple decimal value (signed)
		val = int(value)
		if (val < -(1 << 15)) or (val >= (1 << 15)):
			print('# Error: signed value ' + value[1] + ' does not fit into 16 bits')
		return int(value)

def getAddressValue(address):
	if isTag(address): # tag
		return getLabelValue(address)
	else:
		return getIntValue(address)

def getLabelValue(label):
	if firstPass:
		return 0
	elif label in labels:
		return labels[label]
	else:
		print('# Error: unknown label ' + label)
		sys.exit(1)

# Generate opcode for ldr instructions
def generateLDR(instr):
	global pc
	
	rx = instr[1]
	adr = instr[2]
	if hasStructure(adr) and adr[0] != '0x': # register or register + offset
		if len(adr) == 2:   # register + offset (not supported in current processor)
			offset = getIntValue(adr[1])
			ry = adr[0]
			mode = 1
		else:               # register only
			offset = 0
			ry = adr[0]
			mode = 0
	else:               # address
		offset = getIntValue(adr)
		ry = ['r', '0']
		mode = 1
	code = (opcodes[instr[0]] << fieldshifts['opcode']) \
	     | (mode << fieldshifts['mode']) \
	     | (int(rx[1]) << fieldshifts['rx']) \
	     | (int(ry[1]) << fieldshifts['ry'])
	if mode == 0:
		pc += 1
		return "{:04X}".format(code)
	else:
		pc += 2
		return ("{:04X}".format(code), "{:04X}".format(offset&0xFFFF))

# Generate opcode for str instructions
def generateSTR(instr):
	global pc
	
	rz = instr[1]
	adr = instr[2]
	if hasStructure(adr) and adr[0] != '0x': # register or register + offset
		if len(adr) == 2:   # register + offset (not supported in current processor)
			offset = getIntValue(adr[1])
			ry = adr[0]
			mode = 1
		else:               # register only
			offset = 0
			ry = adr[0]
			mode = 0
	else:               # address
		offset = getIntValue(adr)
		ry = ['r', '0']
		mode = 1
	code = (opcodes[instr[0]] << fieldshifts['opcode']) \
	     | (mode << fieldshifts['mode']) \
	     | (int(ry[1]) << fieldshifts['ry']) \
	     | (int(rz[1]) << fieldshifts['rz'])
	if mode == 0:
		pc += 1
		return "{:04X}".format(code)
	else:
		pc += 2
		return ("{:04X}".format(code), "{:04X}".format(offset&0xFFFF))

# Generate opcode for mov instructions
def generateMOV(instr):
	global pc
	
	rx = instr[1]
	src = instr[2]
	if hasStructure(src) and (src[0] == 'r'):  # register
		code = (opcodes['mov'] << fieldshifts['opcode']) \
			 | (0 << fieldshifts['mode']) \
			 | (int(rx[1]) << fieldshifts['rx']) \
			 | (int(src[1]) << fieldshifts['ry'])
		pc += 1
		return ("{:04X}".format(code))
	else:                                      # immediate value
		val = getIntValue(src[1])
		code = (opcodes['mov'] << fieldshifts['opcode']) \
			 | (1 << fieldshifts['mode']) \
			 | (int(rx[1]) << fieldshifts['rx'])
		pc += 2
		return ("{:04X}".format(code), "{:04X}".format(val&0xFFFF))

# Generate opcode for cmp instructions
def generateCMP(instr):
	global pc
	
	ry = instr[1]
	src = instr[2]
	if hasStructure(src) and (src[0] == 'r'):  # register
		code = (opcodes['cmp'] << fieldshifts['opcode']) \
			 | (0 << fieldshifts['mode']) \
			 | (int(ry[1]) << fieldshifts['ry']) \
			 | (int(src[1]) << fieldshifts['rz'])
		pc += 1
		return ("{:04X}".format(code))
	else:                                      # immediate value
		val = getIntValue(src[1])
		if val < 0:
			val = (1 << 16) - val
		code = (opcodes['cmp'] << fieldshifts['opcode']) \
			 | (1 << fieldshifts['mode']) \
			 | (int(ry[1]) << fieldshifts['ry'])
		pc += 2
		return ("{:04X}".format(code), "{:04X}".format(val))

# Generate opcode for add, sub, or, and instructions
def generateARITH(instr):
	global pc
	
	rx = instr[1]
	ry = instr[2]
	src = instr[3]
	if hasStructure(src) and (src[0] == 'r'):  # register
		code = (opcodes[instr[0]] << fieldshifts['opcode']) \
			 | (0 << fieldshifts['mode']) \
			 | (int(rx[1]) << fieldshifts['rx']) \
			 | (int(src[1]) << fieldshifts['rz']) \
			 | (int(ry[1]) << fieldshifts['ry'])
		pc += 1
		return ("{:04X}".format(code))
	else:                                      # immediate value
		val = getIntValue(src[1])
		if val < 0:
			val = (1 << 16) - val
		code = (opcodes[instr[0]] << fieldshifts['opcode']) \
			 | (1 << fieldshifts['mode']) \
			 | (int(rx[1]) << fieldshifts['rx']) \
			 | (int(ry[1]) << fieldshifts['ry'])
		pc += 2
		return ("{:04X}".format(code), "{:04X}".format(val))

# Generate opcode for beq, blt and b instructions
def generateBRANCH(instr):
	global pc
	
	if hasStructure(instr[1]) and (instr[1][0] == 'r'): # branch to register
		rz = instr[1]
		code = (opcodes[instr[0]] << fieldshifts['opcode']) \
		     | (0 << fieldshifts['mode']) \
		     | (int(rz[1]) << fieldshifts['rz'])
		pc += 1
		return "{:04X}".format(code)
	else:
		baddr = getAddressValue(instr[1])
		code = (opcodes[instr[0]] << fieldshifts['opcode']) \
			 | (1 << fieldshifts['mode'])
		pc += 2
		return ("{:04X}".format(code), "{:04X}".format(baddr))

# Generate opcode for the bl instruction
def generateBRANCHLINK(instr):
	global pc
	
	rx = instr[1]
	if hasStructure(instr[2]) and (instr[2][0] == 'r'): # branch to register
		rz = instr[1]
		code = (opcodes[instr[0]] << fieldshifts['opcode']) \
		     | (0 << fieldshifts['mode']) \
		     | (int(rx[1]) << fieldshifts['rx']) \
		     | (int(rz[1]) << fieldshifts['rz'])
		pc += 1
		return "{:04X}".format(code)
	else:
		baddr = getAddressValue(instr[2])
		code = (opcodes[instr[0]] << fieldshifts['opcode']) \
			 | (1 << fieldshifts['mode']) \
		     | (int(rx[1]) << fieldshifts['rx'])
		pc += 2
		return ("{:04X}".format(code), "{:04X}".format(baddr))

# Generate code for Set Memory Word pseudo instruction
def generateSMW(instr):
	global pc
	
	value = getIntValue(instr[1])
	pc += 1
	if value < 0 :
		return ("{:04X}".format((1<<16) - value))
	else:
		return ("{:04X}".format(value))

# Generate code for Reserve Memory Words pseudo instruction
def generateRMW(instr):
	global pc
	
	value = getIntValue(instr[1])
	if (value < 0):
		print('# Error: cannot reserve a negative ' + str(value) + ' number of memory words')
	pc += value
	return ('RMW', value)

# Print an instruction argument in the listing
def printarg(arg):
	if hasStructure(arg):
		if arg[0] == 'r':
			return 'r'+arg[1]
		elif arg[0] == '#':
			if hasStructure(arg[1]):
				return '#'+printarg(arg[1])
			else:
				return '#'+arg[1]
		elif arg[0] == '0x':
			return arg[0]+arg[1]
		elif len(arg) == 1:
			return '['+printarg(arg[0])+']'
		else:
			return '['+printarg(arg[0])+','+printarg(arg[1])+']'
	return str(arg)

# Print an instruction line in the listing
def printline(line):
	out = ''
	idx = 0
	if line[0][0] == '@':
		out += line[0][0] + line[0][1] + ' '*(maxlabellen - len(line[0][1]))
		idx = 1
	else:
		out += ' '*(maxlabellen + 1)
	
	out += ' ' + line[idx][0] + ' '
	
	for i in range(1, len(line[idx])):
		if (i > 1):
			out += ','
		out += printarg(line[idx][i])
	return out

# Parse the source file
p = program.parseFile(sys.argv[1], parseAll=True)

# Compute the name of the output files (.mem and .lst)
dotpos = sys.argv[1].rfind('.')
if dotpos == -1:
	binfname = sys.argv[1] + '.mem'
	lstfname = sys.argv[1] + '.lst'
else:
	binfname = sys.argv[1][0:dotpos] + '.mem'
	lstfname = sys.argv[1][0:dotpos] + '.lst'
binfile = open(binfname, 'w')
binfile.write('v2.0 raw')
lstfile = open(lstfname, 'w')

def makeBinSeparator(pc, binfile):
	if (pc % 8) == 0:
		binfile.write('\n')
	else:
		binfile.write(' ')

def performOutput(line, bcode, pc):
	if hasStructure(bcode): # two word instruction
		if (bcode[0] == 'RMW'):
			for i in range(bcode[1]):
				makeBinSeparator(pc+i, binfile)
				binfile.write("0000")
			lstfile.write("{:04X} 0000 {}\n".format(pc, printline(line)))
		else:
			makeBinSeparator(pc, binfile)
			binfile.write(bcode[0])
			lstfile.write("{:04X} {} {}\n".format(pc, bcode[0], printline(line)))
			makeBinSeparator(pc+1, binfile)
			binfile.write(bcode[1])
			lstfile.write("     {}\n".format(bcode[1]))
	else:                   # single word instruction
		makeBinSeparator(pc, binfile)
		binfile.write(bcode)
		lstfile.write("{:04X} {} {}\n".format(pc, bcode, printline(line)))

def dispatchInstr(line):
	global firstPass, pc
	
	instrpc = pc
	idx = 0
	if line[0][0] == '@':
		idx += 1
	op = line[idx][0]
	if op == 'ldr':
		bcode = generateLDR(line[idx])
	elif op == 'str':
		bcode = generateSTR(line[idx])
	elif op == 'mov':
		bcode = generateMOV(line[idx])
	elif op == 'add':
		bcode = generateARITH(line[idx])
	elif op == 'sub':
		bcode = generateARITH(line[idx])
	elif op == 'cmp':
		bcode = generateCMP(line[idx])
	elif op == 'blt':
		bcode = generateBRANCH(line[idx])
	elif op == 'beq':
		bcode = generateBRANCH(line[idx])
	elif op == 'b':
		bcode = generateBRANCH(line[idx])
	elif op == 'bl':
		bcode = generateBRANCHLINK(line[idx])
	elif op == 'smw':
		bcode = generateSMW(line[idx])
	elif op == 'rmw':
		bcode = generateRMW(line[idx])
	elif hasStructure(op):   # pseudo instruction expansion
		firstInstr = True
		for sub in line[idx]:
			# Attach label of pseudo instruction to first instruction in expansion
			if firstInstr and idx > 0:
				firstInstr = False
				dispatchInstr([line[0], sub])
			else:
				dispatchInstr([sub])
		return
	else:
		print('# Error: unsupported instruction ' + str(line[idx][0]))
		sys.exit(1)
	if not(firstPass):
		performOutput(line, bcode, instrpc)
	return

# Length of longest label (for formatting the listing)
maxlabellen = 0
pc = 0
# Firstly, compute the address of labels
for line in p:
	idx = 0
	if line[0][0] == '@':
		labels[line[0][1]] = pc
		idx = 1
		l = len(line[0][1])
		if l > maxlabellen:
			maxlabellen = l
	dispatchInstr(line)

# Now, do the assembly
pc = 0
firstPass = False

for line in p:
	dispatchInstr(line)

binfile.close()
lstfile.close()
exit()
