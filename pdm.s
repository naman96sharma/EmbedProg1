 	.syntax unified
 	.cpu cortex-m3
 	.thumb
 	.align 2
 	.global	pdm
 	.thumb_func
	 
pdm:
Push {R1-R7, R14} @Pushing the register values and LR value
MOV R3, R1 @Since the M value is needed for the ELEMENT, we use R3 as the changing "j" value instead
LDR R4, =0
SUB R3, R3, #1 @Reducing R3 and R2 by 1 so the the matrix is
SUB R2, R2, #1 @numbered starting from 0 (ease in calculation)
Loop:
	BL ELEMENT		@The loop starts from the last
	ADD R4, R9, R4  @element in the row and adds upto
	SUBS R3, R3, #1 @the first element in the row.
	BGE Loop
MOV R3, R2
BL ELEMENT @Extracting the value at position (m,m) of matrix
LDR R6, =#10000
MUL R9, R9, R6
UDIV R0, R9, R4
Pop {R1-R7, R14}
	BX	LR

ELEMENT:
Push {R1-R7, R14}
LDR R6, =4
MUL R2, R2, R1
MUL R2, R6, R2
MLA R3, R3, R6, R2
ADD R3, R0, R3
LDR R9, [R3]
Pop {R1-R7, R14}
	BX	LR
