# SPDX-FileCopyrightText: 2023 Max Sikström
# SPDX-License-Identifier: MIT

# Copyright © 2023 Max Sikström
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gdb
from .common import *
import traceback

# Architecture reference manuals:
#
# ARMv6-M https://developer.arm.com/documentation/ddi0419/latest/
# ARMv7-M https://developer.arm.com/documentation/ddi0403/latest/
# ARMv8-M https://developer.arm.com/documentation/ddi0553/latest/
#
# Implmementaitons:
#
# ARMv6-M
# M0: https://developer.arm.com/documentation/dui0497/a/cortex-m0-peripherals/system-control-block
# M0+: https://developer.arm.com/documentation/dui0662/b/Cortex-M0--Peripherals/System-Control-Block
# M1: https://developer.arm.com/documentation/ddi0413/d/system-control/about-system-control
#
# ARMv7-M
# M3: https://developer.arm.com/documentation/dui0552/a/cortex-m3-peripherals/system-control-block
# M4: https://developer.arm.com/documentation/100166/0001/System-Control/System-control-registers
# M7: https://developer.arm.com/documentation/dui0646/c/Cortex-M7-Peripherals/System-control-block
#
# ARMv8-M
# TODO: Cache registers: CLIDR, CTR, CCSIDR, CSSEL
# M23: https://developer.arm.com/documentation/dui1095/a/Cortex-M23-Peripherals/System-Control-Space
# M33: https://developer.arm.com/documentation/100235/0004/the-cortex-m33-peripherals/system-control-block


def get_scb_regs(model):
    enum_val_en_dis = [
        (0, True, "Normal operation", None),
        (1, False, "Disabled", None)
    ]
    CPACR_enum_fields = [
        (0b00, True, "Access denied",
         "Any attempted access generates a NOCP UsageFault."),
        (0b01, False, "Privileged access only.",
         "An unprivileged access generates a NOCP UsageFault."),
        (0b10, False, "Reserved.", None),
        (0b11, False, "Full access.", None),
    ]

    return {
        'SCB': filt(model, [
            ('v8', RegisterDef("REVIDR", "Revision ID Register", 0xE000ECFC, 4, [
                FieldBitfield("imp. defined", 0, 32),
            ])),
            (None, RegisterDef("CPUID", "CPUID Base Register", 0xE000ED00, 4, [
                FieldBitfieldEnum("Implementer", 24, 8, [
                    (0x41, True, "ARM", None)
                ], "Implementer code assigned by Arm"),
                FieldBitfieldMap("Variant", 20, 4,
                                 lambda n: "Revision: r%dpX" % (n,), always=True),
                FieldBitfieldEnum("Architecture", 16, 4, filt(model, [
                    ("v6", (0xc, False, "ARMv6-M", None)),
                    ("v7", (0xf, False, "ARMv7-M", None)),
                    ("v8", (0xc, False, "ARMv8-M without main extension", None)),
                    ("v8", (0xf, False, "ARMv8-M with main extension", None)),
                ])),
                FieldBitfieldEnum("PartNo", 4, 12, [
                    (0xc20, False, "Cortex-M0", None),
                    (0xc60, False, "Cortex-M0+", None),
                    (0xc21, False, "Cortex-M1", None),
                    (0xc23, False, "Cortex-M3", None),
                    (0xc24, False, "Cortex-M4", None),
                    (0xc27, False, "Cortex-M7", None),
                    (0xd20, False, "Cortex-M23", None),
                    (0xd21, False, "Cortex-M33", None),
                ]),
                FieldBitfieldMap("Revision", 0, 4,
                                 lambda n: "Patch: rXp%d" % (n,), always=True),
            ])),
            (None, RegisterDef("ICSR", "Interrupt Control and State Register", 0xE000ED04, 4, filt(model, [
                (None, FieldBitfield("NMIPENDSET", 31, 1)),
                (None, FieldBitfield("PENDSVSET", 28, 1)),
                (None, FieldBitfield("PENDSTSET", 26, 1)),
                ('v8', FieldBitfield("STTNS", 24, 1,
                                     "SysTick Targets Non-secure. Controls whether in a single SysTick implementation, the SysTick is Secure or Non-secure.")),
                (None, FieldBitfield("ISRPREEMPT", 23, 1,
                                     "Indicates whether a pending exception will be serviced on exit from debug halt state")),
                (None, FieldBitfield("ISRPENDING", 22, 1,
                                     "Indicates whether an external interrupt, generated by the NVIC, is pending")),
                (None, FieldBitfield("VECTPENDING", 12, 6,
                                     "The exception number of the highest priority pending and enabled interrupt")),
                ('v7,v8', FieldBitfield("RETTOBASE", 11, 1,
                                        "In Handler mode, indicates whether there is an active exception other than the exception indicated by the current value of the IPSR")),
                (None, FieldBitfield("VECTACTIVE", 0, 8)),
            ]))),
            (None, RegisterDef("VTOR", "Vector Table Offset Register", 0xE000ED08, 4, [
                FieldBitfield("TBLOFF", 7, 25,
                              "Bits[31:7] of the vector table address")
            ])),
            (None, RegisterDef("AIRCR", "Application Interrupt and Reset Control Register", 0xE000ED0C, 4, filt(model, [
                (None, FieldBitfieldEnum("VECTKEYSTAT", 16, 16, [
                    (0x05fa, False, "Register writes must write 0x05FA to this field, otherwise the write is ignored", None),
                    (0xfa05, True, "On reads, returns 0xFA05", None),
                ])),
                (None, FieldBitfieldEnum("ENDIANNESS", 15, 1, [
                    (0, False, "Little Endian", None),
                    (1, False, "Big Endian", None),
                ])),
                ('v8', FieldBitfieldEnum("PRIS", 14, 1, [
                    (0, True, "Sec and Non-sec are identical",
                     "Priority ranges of Secure and Non-secure exceptions are identical."),
                    (1, False, "Non-sec are de-prioritized",
                     "Non-secure exceptions are de-prioritized."),
                ], "Prioritize Secure exceptions. The value of this bit defines whether Secure exception priority boosting is enabled.")),
                ('v8', FieldBitfieldEnum("BFHFNMINS", 13, 1, [
                    (0, True, "BusFault, HardFault, and NMI are Secure.", None),
                    (1, False, "BusFault and NMI are Non-secure",
                     "BusFault and NMI are Non-secure and exceptions can target Non-secure HardFault."),
                ], "BusFault, HardFault, and NMI Non-secure enable.")),
                ('v7,v8', FieldBitfield(
                    "PRIGROUP", 8, 3, "Priority grouping, indicates the binary point position.")),
                ('v8', FieldBitfieldEnum("IESB", 5, 1, [
                    (0, True, "No Implicit ESB.", None),
                    (1, False, "Implicit ESB are enabled.", None),
                ], "Implicit ESB Enable. This bit indicates and allows modification of whether an implicit Error Synchronization Barriers occurs around lazy Floating-point state preservation, and on every exception entry and return.")),
                ('v8', FieldBitfieldEnum("DIT", 4, 1, [
                    (0, True, "no statement about the timing",
                     "The architecture makes no statement about the timing properties of any instructions."),
                    (1, False, "load/store timing is data independent",
                     "The architecture requires that the timing of every load and store instruction is insensitive to the value of the data being loaded or stored."),
                ], "Data Independent Timing. This bit indicates and allows modification of whether for the selected Security state data independent timing operations are guaranteed to be timing invariant with respect to the data values being operated on.")),
                ('v8', FieldBitfieldEnum("SYSRESETREQS", 3, 1, [
                    (0, True, "SYSRESETREQ available to both Security states", None),
                    (1, False, "SYSRESETREQ only available to Secure state", None),
                ], "System reset request Secure only.")),
                (None, FieldBitfield("SYSRESETREQ", 2, 1, "System Reset Request")),
            ]))),
            (None, RegisterDef("SCR", "System Control Register", 0xE000ED10, 4, filt(model, [
                (None, FieldBitfield(
                    "SEVONPEND", 4, 1, "Determines whether an interrupt transition from inactive state to pending state is a wakeup event")),
                ('v8', FieldBitfield(
                    "SLEEPDEEPS", 3, 1, "Sleep deep secure. This field controls whether the SLEEPDEEP bit is only accessible from the Secure state.")),
                (None, FieldBitfield(
                    "SLEEPDEEP", 2, 1, "Provides a qualifying hint indicating that waking from sleep might take longer")),
                (None, FieldBitfield(
                    "SLEEPONEXIT", 1, 1, "Determines whether, on an exit from an ISR that returns to the base level of execution priority, the processor enters a sleep state")),
            ]))),
            (None, RegisterDef("CCR", "Configuration and Control Register", 0xE000ED14, 4, filt(model, [
                ('v8', FieldBitfield("TRD", 20, 1, "Thread reentrancy disabled.")),
                ('v8', FieldBitfield("LOB", 19, 1,
                 "Loop and branch info cache enable.")),
                ('v7,v8', FieldBitfield("BP", 18, 1, "Branch prediction enable bit.")),
                ('v7,v8', FieldBitfield("IC", 17, 1, "Instruction cache enable bit.")),
                ('v7,v8', FieldBitfield("DC", 16, 1, "Cache enable bit.")),
                ('v8', FieldBitfield("STKOFHFNMIGN", 10, 1,
                                     "Stack overflow in HardFault and NMI ignore.")),
                ('v6,v7', FieldBitfieldEnum("STKALIGN", 9, 1, [
                    (0, True, "4 bytes SP alignment",
                     "Guaranteed SP alignment is 4-byte, no SP adjustment is performend."),
                    (1, False, "8 byte SP alignment",
                     "8-byte alignment guaranteed, SP adjusted if necessary."),
                ], "Determines whether the exception entry sequence guarantees 8-byte stack frame alignment")),
                ('v7,v8', FieldBitfieldEnum("BFHFNMIGN", 8, 1, [
                    (0, True, "Precise data access fault causes a lockup", None),
                    (1, False, "Handler ignores the fault.", None),
                ], "Determines the effect of precise data access faults on handlers running at priority -1 or priority -2")),
                ('v7,v8', FieldBitfield("DIV_0_TRP", 4, 1,
                                        "Controls the trap on divide by 0")),
                ('v6,v7,v8', FieldBitfield("UNALIGN_TRP", 3, 1,
                                           "Controls the trapping of unaligned word or halfword accesses")),
                ('v7,v8', FieldBitfield("USERSETMPEND", 1, 1,
                                        "Controls whether unprivileged software can access the STIR")),
                ('v7', FieldBitfield("NONBASETHRDENA", 0, 1,
                                     "Controls whether the processor can enter Thread mode with exceptions active")),
            ]))),
            ('v7', RegisterDef("SHPR1", "System Handler Priority Register 1", 0xE000ED18, 4, filt(model, [
                (None, FieldBitfield("PRI_4 - MemManage", 0, 8,
                                     "Priority of system handler 4, MemManage.")),
                (None, FieldBitfield("PRI_5 - BusFault", 8, 8,
                                     "Priority of system handler 5, BusFault.")),
                (None, FieldBitfield("PRI_6 - UsageFault", 16, 8,
                                     "Priority of system handler 6, UsageFault.")),
                ('v6,v7', FieldBitfield("PRI_7", 24, 8,
                                        "Reserved for priority of system handler 7")),
                ('v8', FieldBitfield("PRI_7 - SecureFault", 24, 8,
                                     "Priority of system handler 7, SecureFault.")),
            ]))),
            (None, RegisterDef("SHPR2", "System Handler Priority Register 2", 0xE000ED1C, 4, [
                FieldBitfield("PRI_8", 0, 8,
                              "Reserved for priority of system handler 8."),
                FieldBitfield("PRI_9", 8, 8,
                              "Reserved for priority of system handler 9."),
                FieldBitfield("PRI_10", 16, 8,
                              "Reserved for priority of system handler 10."),
                FieldBitfield("PRI_11 - SVCall", 24, 8,
                              "Priority of system handler 11, SVCall.")
            ])),
            (None, RegisterDef("SHPR3", "System Handler Priority Register 3", 0xE000ED20, 4, filt(model, [
                ('v6', FieldBitfield("PRI_12", 0, 8,
                                     "Reserved for priority of system handler 12.")),
                ('v7,v8', FieldBitfield("PRI_12 - DebugMonitor", 0, 8,
                                        "Priority of system handler 12, DebugMonitor.")),
                (None, FieldBitfield("PRI_13", 8, 8,
                                     "Reserved for priority of system handler 13.")),
                (None, FieldBitfield("PRI_14 - PendSV", 16, 8,
                                     "Priority of system handler 14, PendSV.")),
                (None, FieldBitfield("PRI_15 - SysTick", 24, 8,
                                     "Priority of system handler 15, SysTick."))
            ]))),
            ('v7,v8', RegisterDef("SHCSR", "System Handler Control and State Register", 0xE000ED24, 4, filt(model, [
                ('v8', FieldBitfield("HARDFAULTPENDED", 21, 1,
                                     "Indicates if HardFault is pending.")),
                ('v8', FieldBitfield("SECUREFAULTPENDED", 20, 1,
                                     "Indicates if SecureFault is pending.")),
                ('v8', FieldBitfield("SECUREFAULTENA", 19, 1,
                                     "Indicates if SecureFault is enabled.")),
                (None, FieldBitfield("USGFAULTENA", 18, 1,
                                     "Indicates if UsageFault is enabled.")),
                (None, FieldBitfield("BUSFAULTENA", 17, 1,
                                     "Indicates if BusFault is enabled.")),
                (None, FieldBitfield("MEMFAULTENA", 16, 1,
                                     "Indicates if MemFault is enabled.")),
                (None, FieldBitfield("SVCALLPENDED", 15, 1,
                                     "Indicates if SVCall is pending.")),
                (None, FieldBitfield("BUSFAULTPENDED", 14, 1,
                                     "Indicates if BusFault is pending")),
                (None, FieldBitfield("MEMFAULTPENDED", 13, 1,
                                     "Indicates if MemFault is pending")),
                (None, FieldBitfield("USGFAULTPENDED", 12, 1,
                                     "Indicates if UsageFault is pending")),
                (None, FieldBitfield("SYSTICKACT", 11, 1,
                                     "Indicates if SysTick is active")),
                (None, FieldBitfield("PENDSVACT", 10, 1,
                                     "Indicates if PendSV is active")),
                (None, FieldBitfield("MONITORACT", 8, 1,
                                     "Indicates if Monitor is active")),
                (None, FieldBitfield("SVCALLACT", 7, 1,
                                     "Indicates if SVCall is active")),
                ('v8', FieldBitfield("NMIACT", 5, 1,
                                     "Indicates if NMI exception is active")),
                ('v8', FieldBitfield("SECUREFAULTACT", 4, 1,
                                     "Indicates if SecureFault is active")),
                (None, FieldBitfield("USGFAULTACT", 3, 1,
                                     "Indicates if UsageFault is active")),
                ('v8', FieldBitfield("HARDFAULTACT", 2, 1,
                                     "Indicates if HardFault is active")),
                (None, FieldBitfield("BUSFAULTACT", 1, 1,
                                     "Indicates if BusFault is active")),
                (None, FieldBitfield("MEMFAULTACT", 0, 1,
                                     "Indicates if MemFault is active")),
            ]))),
            ('v7,v8', RegisterDef("CFSR", "Configurable Fault Status Register", 0xE000ED28, 4, filt(model, [
                (None, FieldBitfield("MMFSR",       0,    8,
                                     "MemManage Fault Status Register", always=True)),
                (None, FieldBitfield("MMARVALID",   7+0,  1,
                                     "Indicates if MMFAR has valid contents.")),
                (None, FieldBitfield("MLSPERR",     5+0,  1,
                                     "Indicates if a MemManage fault occurred during FP lazy state preservation.")),
                (None, FieldBitfield("MSTKERR",     4+0,  1,
                                     "Indicates if a derived MemManage fault occurred on exception entry.")),
                (None, FieldBitfield("MUNSTKERR",   3+0,  1,
                                     "Indicates if a derived MemManage fault occurred on exception return.")),
                (None, FieldBitfield("DACCVIOL",    1+0,  1,
                                     "Data access violation. The MMFAR shows the data address that the load or store tried to access.")),
                (None, FieldBitfield("IACCVIOL",    0+0,  1,
                                     "MPU or Execute Never (XN) default memory map access violation on an instruction fetch has occurred.")),
                (None, FieldBitfield("BFSR",        8,    8,
                                     "BusFault Status Register", always=True)),
                (None, FieldBitfield("BFARVALID",   7+8,  1,
                                     "Indicates if BFAR has valid contents.")),
                (None, FieldBitfield("LSPERR",      5+8,  1,
                                     "Indicates if a bus fault occurred during FP lazy state preservation.")),
                (None, FieldBitfield("STKERR",      4+8,  1,
                                     "Indicates if a derived bus fault has occurred on exception entry.")),
                (None, FieldBitfield("UNSTKERR",    3+8,  1,
                                     "Indicates if a derived bus fault has occurred on exception return.")),
                (None, FieldBitfield("IMPRECISERR", 2+8,  1,
                                     "Indicates if imprecise data access error has occurred.")),
                (None, FieldBitfield("PRECISERR",   1+8,  1,
                                     "Indicates if a precise data access error has occurred, and the processor has written the faulting address to the BFAR.")),
                (None, FieldBitfield("IBUSERR",     0+8,  1,
                                     "Indicates if a bus fault on an instruction prefetch has occurred. The fault is signaled only if the instruction is issued.")),
                (None, FieldBitfield("UFSR",        16,  16,
                                     "UsageFault Status Register", always=True)),
                (None, FieldBitfield("DIVBYZERO",   9+16, 1,
                                     "Indicates if divide by zero error has occurred.")),
                (None, FieldBitfield("UNALIGNED",   8+16, 1,
                                     "Indicates if unaligned access error has occurred.")),
                ('v8', FieldBitfield("STKOF",       4+16, 1,
                                     "Indicates if a stack overflow has occurred.")),
                (None, FieldBitfield("NOCP",        3+16, 1,
                                     "Indicates if a coprocessor access error has occurred. This shows that the coprocessor is disabled or not present.")),
                (None, FieldBitfield("INVPC",       2+16, 1,
                                     "Indicates if an integrity check error has occurred on EXC_RETURN.")),
                (None, FieldBitfield("INVSTATE",    1+16, 1,
                                     "Indicates if instruction executed with invalid EPSR.T or EPSR.IT field.")),
                (None, FieldBitfield("UNDEFINSTR",  0+16, 1,
                                     "Indicates if the processor has attempted to execute an undefined instruction.")),
            ]))),
            ('v7,v8', RegisterDef("HFSR", "HardFault Status Register", 0xE000ED2C, 4, [
                FieldBitfield("DEBUGEVT", 31, 1,
                              "Indicates when a Debug event has occurred."),
                FieldBitfield("FORCED", 30, 1,
                              "Indicates that a fault with configurable priority has been escalated to a HardFault exception."),
                FieldBitfield("VECTTBL", 1, 1,
                              "Indicates when a fault has occurred because of a vector table read error on exception processing."),
            ])),
            (None, RegisterDef("DFSR", "Debug Fault Status Register", 0xE000ED30, 4, filt(model, [
                ('v8', FieldBitfieldEnum("PMU", 5, 1, [
                    (0, True, "PMU event has not occurred.", None),
                    (1, False, "PMU event has occurred.", None),
                ], "PMU event. Sticky flag indicating whether a PMU counter overflow event has occurred.")),
                (None, FieldBitfieldEnum("EXTERNAL", 4, 1, [
                    (0, True, "No external debug request debug event", None),
                    (1, False, "External debug request debug event", None),
                ], "Indicates a debug event generated because of the assertion of an external debug request")),
                (None, FieldBitfieldEnum("VCATCH", 3, 1, [
                    (0, True, "No Vector catch triggered", None),
                    (1, False, "Vector catch triggered", None),
                ], "Indicates triggering of a Vector catch")),
                (None, FieldBitfieldEnum("DWTTRAP", 2, 1, [
                    (0, True, "No debug events generated by the DWT", None),
                    (1, False, "At least one debug event generated by the DWT", None),
                ], "Indicates a debug event generated by the DWT")),
                (None, FieldBitfieldEnum("BKPT", 1, 1, [
                    (0, True, "No breakpoint debug event", None),
                    (1, False, "At least one breakpoint debug event", None),
                ], "Indicates a debug event generated by BKPT instruction execution or a breakpoint match in FPB")),
                (None, FieldBitfieldEnum("HALTED", 0, 1, [
                    (0, True, "No halt request debug event", None),
                    (1, False, "Halt request debug event", None),
                ], "Indicates a debug event generated by either C_HALT, C_STEP or DEMCR.MON_STEP")),
            ]))),
            ('v7,v8', RegisterDef("MMFAR", "MemManage Fault Address Register",
                                  0xE000ED34, 4)),
            ('v7,v8', RegisterDef("BFAR", "BusFault Address Register", 0xE000ED38, 4)),
            (None, RegisterDef("AFSR", "Auxiliary Fault Status Register", 0xE000ED3C, 4, [
                FieldBitfield("IMPDEF", 0, 32, "Implemention defined"),
            ])),
            ('v7,v8', RegisterDef("CPACR", "Coprocessor Access Control Register", 0xE000ED88, 4, [
                FieldBitfieldEnum("CP0", 0, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 0"),
                FieldBitfieldEnum("CP1", 2, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 1"),
                FieldBitfieldEnum("CP2", 4, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 2"),
                FieldBitfieldEnum("CP3", 6, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 3"),
                FieldBitfieldEnum("CP4", 8, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 4"),
                FieldBitfieldEnum("CP5", 10, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 5"),
                FieldBitfieldEnum("CP6", 12, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 6"),
                FieldBitfieldEnum("CP7", 14, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 7"),
                FieldBitfieldEnum("CP10 - FPU", 20, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 10"),
                FieldBitfieldEnum("CP11 - FPU", 22, 2, CPACR_enum_fields,
                                  "Access privileges for coprocessor 11"),
            ]))
        ]),
        'AUX': filt(model, [
            (None, RegisterDef("ICTR", "Interrupt Controller Type Register", 0xE000E004, 4, [
                FieldBitfieldMap("INTLINESNUM", 0, 4, lambda v: "%d vectors" % (min(32*(v+1), 496),),
                                 "The total number of interrupt lines supported, as 32*(1+N)")
            ])),
            ('M1', RegisterDef("ACTLR - M1", "Auxiliary Control Register - Cortex M1", 0xE000E008, 4, [
                FieldBitfield("ITCMUAEN", 4, 1,
                              "Instruction TCM Upper Alias Enable."),
                FieldBitfield("ITCMLAEN", 3, 1,
                              "Instruction TCM Lower Alias Enable."),
            ])),
            ('M3', RegisterDef("ACTLR - M3", "Auxiliary Control Register - Cortex M3", 0xE000E008, 4, [
                FieldBitfield("DISFOLD", 2, 1),
                FieldBitfield("DISDEFWBUF", 1, 1),
                FieldBitfield("DISMCYCINT", 0, 1),
            ])),
            ('M4', RegisterDef("ACTLR - M4", "Auxiliary Control Register - Cortex M4", 0xE000E008, 4, [
                FieldBitfield("DISOOFP", 9, 1),
                FieldBitfield("DISFPCA", 8, 1),
                FieldBitfield("DISFOLD", 2, 1),
                FieldBitfield("DISDEFWBUF", 1, 1),
                FieldBitfield("DISMCYCINT", 0, 1),
            ])),
            ('M7', RegisterDef("ACTLR - M7", "Auxiliary Control Register - Cortex M7", 0xE000E008, 4, [
                FieldBitfield("DISFPUISSOPT", 28, 1),
                FieldBitfield("DISCRITAXIRUW", 27, 1),
                FieldBitfield("DISDYNADD", 26, 1),
                FieldBitfield("DISISSCH1", 21, 5, always=True),
                FieldBitfieldEnum(
                    "    VFP", 25, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "might not be issued in channel 1.", None)
                    ], "VFP"),
                FieldBitfieldEnum(
                    "    MAC and MUL", 24, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "might not be issued in channel 1.", None)
                    ], "Integer MAC and MUL"),
                FieldBitfieldEnum(
                    "    Loads to PC", 23, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "might not be issued in channel 1.", None)
                    ], "Loads to PC"),
                FieldBitfieldEnum(
                    "    Indirect branches", 22, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "might not be issued in channel 1.", None)
                    ], "Indirect branches, but not loads to PC"),
                FieldBitfieldEnum(
                    "    Direct branches", 21, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "might not be issued in channel 1.", None)
                    ], "Direct branches"),
                FieldBitfield("DISDI", 16, 5, always=True),
                FieldBitfieldEnum(
                    "    VFP", 20, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "Dual issue disabled",
                         "Nothing can be dual-issued when this instruction type is in channel 0.")
                    ], "VFP"),
                FieldBitfieldEnum(
                    "    Integer MAC and MUL", 19, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "Dual issue disabled",
                         "Nothing can be dual-issued when this instruction type is in channel 0.")
                    ], "Integer MAC and MUL"),
                FieldBitfieldEnum(
                    "    Loads to PC", 18, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "Dual issue disabled",
                         "Nothing can be dual-issued when this instruction type is in channel 0.")
                    ], "Loads to PC"),
                FieldBitfieldEnum(
                    "    Indirect branches", 17, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "Dual issue disabled",
                         "Nothing can be dual-issued when this instruction type is in channel 0.")
                    ], "Indirect branches, but not loads to PC"),
                FieldBitfieldEnum(
                    "    Direct branches", 16, 1, [
                        (0, True, "Normal operation", None),
                        (1, False, "Disabled", None)
                    ], "Direct branches"),
                FieldBitfield("DISCRITAXIRUR", 15, 1),
                FieldBitfield("DISBTACALLOC", 14, 1),
                FieldBitfield("DISBTACREAD", 13, 1),
                FieldBitfield("DISITMATBFLUSH", 12, 1),
                FieldBitfield("DISRAMODE", 11, 1),
                FieldBitfield("FPEXCODIS", 10, 1),
                FieldBitfield("DISFOLD", 2, 1),
            ])),
            ('M33', RegisterDef("ACTLR - M33", "Auxiliary Control Register - Cortex M7", 0xE000E008, 4, [
                FieldBitfield("EXTEXCLALL", 29, 1),
                FieldBitfield("DISITMATBFLUSH", 12, 1),
                FieldBitfield("FPEXCODIS", 10, 1),
                FieldBitfield("DISOOFP", 9, 1),
                FieldBitfield("DISFOLD", 2, 1),
            ])),
        ])
    }


class ArmToolsSCB (ArgCommand):
    """Dump of ARM Cortex-M SCB - System Control Block

Usage: arm scb [/habf]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values
Modifier /b prints bitmasks in binary instead of hex
Modifier /f force printing fields from all Cortex-M models
"""

    def __init__(self):
        super().__init__('arm scb', gdb.COMMAND_DATA)
        self.add_mod('h', 'descr')
        self.add_mod('a', 'all')
        self.add_mod('b', 'binary')
        self.add_mod('f', 'force')

    def invoke(self, argument, from_tty):
        args = self.process_args(argument)
        if args is None:
            self.print_help()
            return

        try:
            base = 1 if args['binary'] else 4

            inf = gdb.selected_inferior()

            # Detect CPU type, convert to a useful key for dicts
            CPUID = read_reg(inf, 0xE000ED00, 4)
            model = {
                "4100c200": ["M0", "v6"],
                "4100c600": ["M0+", "v6"],
                "4100c210": ["M1", "v6"],
                "4100c230": ["M3", "v7"],
                "4100c240": ["M4", "v7"],
                "4100c270": ["M7", "v7"],
                # TODO: support ARMv8-M, for now pretend it's v7, since it's similar
                "4100d200": ["M23", "v8"],
                "4100d210": ["M33", "v8"],
            }.get(format_int(CPUID & 0xff00fff0, 32), None)

            print("SCB for Cortex-%s - ARM%s-M" %
                  ((model[0], model[1]) if model else ("XX", "XX")))

            if args['force']:
                print("(printing fields from all Cortex-M models)")
                model = None

            regs = get_scb_regs(set(model) if model is not None else None)

            for sect_name, sect_regs in regs.items():
                print("")
                print("%s registers:" % (sect_name,))
                for reg in sect_regs:
                    reg.dump(inf, args['descr'], base=base, all=args['all'])
        except:
            traceback.print_exc()
