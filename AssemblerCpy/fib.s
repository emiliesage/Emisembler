/*
    Start with 0 and 1 as the start of the fibonaci sequence
    Print both to the screen
*/
LDI R0, 0x00 
OUT R0
LDI R1, 0x01
OUT R1
LOOP: #Loop label
    MOV R2, R1 #Use R2 as a place holder for current fibonaci number
    ADD R1, R1, R0 #Add previous and current fibonaci number
    MOV R0, R2 #Store current as previous
    OUT R1 #Output current 
    CPI R1, 0x23 #Compare to 35
    BGT END #Branch if greater than 35
    JMP LOOP #Loop
END: #End label
    HLT 