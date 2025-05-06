.ascii " Bottles of Beer on the Wall\n0"
LDI R2, 0x63
LOOP:
    LDI R0, 0x00
    LDI R1, 0x00
    LDI R3, 0x01
    OUT R2
    ADDI R2, 0xFF
    CPI R2, 0x00
    BEQ END
    JMP PRINT

PRINT:
    LDIRP R3, (R01)
    ADDIW R01, 0x0001
    OUTA R3
    CPI R3, 0x00
    BEQ LOOP
    JMP PRINT

END:
    HLT
