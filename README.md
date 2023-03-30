arm-gdb
=======

Tools for inspecting ARM Cortex-M registers within GDB

Currently supported:
* SCB - System Control Block
* SysTick
* NVIC - Nested Vectored Interrupt Controller

Install
-------

```
pip install arm-gdb
```

Run
---

Start GDB and run
```
python import arm_gdb
```

Or add that line to `~/.gdbinit`

Exmaples
--------

Dump of ARM System Control Block, with bitmask descriptions
```
(gdb) arm scb -d
ACTLR                            = 00000000                   // Auxiliary Control Register
CPUID                            = 410fc241                   // CPUID Base Register
    Revision                       00000001 - 1
    PartNo                         0000c240 - c24
    Constant                       000f0000 - f
    Implementer                    41000000 - 41
ICSR                             = 0040080b                   // Interrupt Control and State Register
    VECTACTIVE                     0000000b - 0b
    RETTOBASE                      00000800 - 1
    ISRPENDING                     00400000 - 1
VTOR                             = 00000000                   // Vector Table Offset Register
AIRCR                            = fa050000                   // Application Interrupt and Reset Control Register
    VECTKEY                        fa050000 - fa05
SCR                              = 00000010                   // System Control Register
    SEVONPEND                      00000010 - 1
CCR                              = 00000200                   // Configuration and Control Register
    STKALIGN                       00000200 - 1
SHPR1                            = 00000000                   // System Handler Priority Register 1
SHPR2                            = 00000000                   // System Handler Priority Register 2
SHPR3                            = 00000000                   // System Handler Priority Register 3
SHCRS                            = 00000080                   // System Handler Control and State Register
    SVCALLACT                      00000080 - 1
CFSR                             = 00000000                   // Configurable Fault Status Register
MMFSR                            =       00                   // MemManage Fault Status Register
MMFAR                            = e000edf8                   // MemManage Fault Address Register
BFSR                             =       00                   // BusFault Status Register
BFAR                             = e000edf8                   // BusFault Address Register
UFSR                             =     0000                   // UsageFault Status Register
HFSR                             = 00000000                   // HardFault Status Register
AFSR                             = 00000000                   // Auxiliary Fault Status Register
```

Dump of ARM SysTick
```
(gdb) arm systick
SYST_CSR                         = 00000004
    CLKSOURCE                      00000004 - 1
SYST_RVR                         = 00000000
SYST_CVR                         = 00000000
SYST_CALIB                       = c0000000
    SKEW                           40000000 - 1
    NOREF                          80000000 - 1
```
... or with descriptions
```
(gdb) arm systick -d
SYST_CSR                         = 00000004                   // SysTick Control and Status Register
    CLKSOURCE                      00000004 - 1
SYST_RVR                         = 00000000                   // SysTick Reload Value Register
SYST_CVR                         = 00000000                   // SysTick Current Value Register
SYST_CALIB                       = c0000000                   // SysTick Calibration Value Register
    SKEW                           40000000 - 1
    NOREF                          80000000 - 1
```

Dump of NVIC list, listing all enabled interrupt handlers, in a redirected
interrupt vector

Default, it checks for functions in the active interrupt vector given VTOR
register. But in for example nRF52840 using their SoftDevice, the interrupts are
forwarded in software to the application for SoftDevice to override.

```
(gdb) arm nvic -V &__isr_vector
IRQn Prio          Handler
 -15    0 en          0002a739 Reset      -
 -14    0 en          0002a761 NMI        -
 -13    0 en          0002bc45 HardFault  HardFault_Handler
  -5   80 en          00027201 SVC        SVC_Handler
  -2    0 en          00027231 PendSV     PendSV_Handler
   0   80 en          00027715 POWER_CLOCK_IRQHandler
   2   60 en          0002c3ed UARTE0_UART0_IRQHandler
  11    0 en          0002a773 -
  17   c0 en pend     0002bd2d RTC1_IRQHandler
  21   40 en          0002bd35 SWI1_EGU1_IRQHandler
  22   c0 en          000279e9 SWI2_EGU2_IRQHandler
  23   a0 en          0002c019 SWI3_EGU3_IRQHandler
  25   80 en          0002a773 -
  32   20 en          0002a773 -
  ```

To use an SVD file from cmsis-svd package database, use:

This loads in the device description under a local name, in this case `nrf` for
faster access in upcoming commands

```
(gdb) arm loaddb nrf Nordic nrf52.svd
(gdb) arm list nrf
FICR       @ 0x10000000
UICR       @ 0x10001000
BPROT      @ 0x40000000
POWER      @ 0x40000000
...
(gdb) arm inspect nrf POWER
POWER.TASKS_CONSTLAT             = 00000000
POWER.TASKS_LOWPWR               = 00000000
POWER.EVENTS_POFWARN             = 00000000
POWER.EVENTS_SLEEPENTER          = 00000001
POWER.EVENTS_SLEEPEXIT           = 00000001
POWER.INTENSET                   = 00000002
    POFWARN                        00000000 - Disabled
    SLEEPENTER                     00000000 - Disabled
    SLEEPEXIT                      00000000 - Disabled
POWER.INTENCLR                   = 00000002
    POFWARN                        00000000 - Disabled
    SLEEPENTER                     00000000 - Disabled
    SLEEPEXIT                      00000000 - Disabled
POWER.RESETREAS                  = 00000008
    RESETPIN                       00000000 - NotDetected
    DOG                            00000000 - NotDetected
    SREQ                           00000000 - NotDetected
    LOCKUP                         00000008 - Detected
    OFF                            00000000 - NotDetected
    LPCOMP                         00000000 - NotDetected
    DIF                            00000000 - NotDetected
    NFC                            00000000 - NotDetected
```