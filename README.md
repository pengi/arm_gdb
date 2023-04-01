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
(gdb) arm scb /h
ACTLR                            = 00000000                   // Auxiliary Control Register
CPUID                            = 410fc241                   // CPUID Base Register
    Revision                       .......1 - 1
    PartNo                         ....c24. - c24
    Constant                       ...f.... - f
    Implementer                    41...... - 41
ICSR                             = 00c21000                   // Interrupt Control and State Register
    VECTPENDING                    ...21... - 21
    ISRPENDING                     ..4..... - 1
    Reserved for Debug use         ..8..... - 1
VTOR                             = 00000000                   // Vector Table Offset Register
AIRCR                            = fa050000                   // Application Interrupt and Reset Control Register
    VECTKEY                        fa05.... - fa05
SCR                              = 00000000                   // System Control Register
CCR                              = 00000200                   // Configuration and Control Register
    STKALIGN                       .....2.. - 1
SHPR1                            = 00000000                   // System Handler Priority Register 1
SHPR2                            = 80000000                   // System Handler Priority Register 2
    PRI_11 - SVCall                80...... - 80
SHPR3                            = 00e00000                   // System Handler Priority Register 3
    PRI_14 - PendSV                ..e0.... - e0
SHCRS                            = 00070000                   // System Handler Control and State Register
    MEMFAULTENA                    ...1.... - 1
    BUSFAULTENA                    ...2.... - 1
    USGFAULTENA                    ...4.... - 1
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
    CLKSOURCE                      .......4 - 1
SYST_RVR                         = 00000000
SYST_CVR                         = 00000000
SYST_CALIB                       = c0000000
    SKEW                           4....... - 1
    NOREF                          8....... - 1
```
... or with descriptions
```
(gdb) arm systick /h
SYST_CSR                         = 00000004                   // SysTick Control and Status Register
    CLKSOURCE                      .......4 - 1
SYST_RVR                         = 00000000                   // SysTick Reload Value Register
SYST_CVR                         = 00000000                   // SysTick Current Value Register
SYST_CALIB                       = c0000000                   // SysTick Calibration Value Register
    SKEW                           4....... - 1
    NOREF                          8....... - 1
```
... or with bitmasks in binary
```
(gdb) arm systick /b
SYST_CSR                         = 00000000000000000000000000000100
    CLKSOURCE                      .............................1.. - 1
SYST_RVR                         = 00000000000000000000000000000000
SYST_CVR                         = 00000000000000000000000000000000
SYST_CALIB                       = 11000000000000000000000000000000
    SKEW                           .1.............................. - 1
    NOREF                          1............................... - 1
```

Dump of NVIC list, listing all enabled interrupt handlers, in a redirected
interrupt vector

Default, it checks for functions in the active interrupt vector given VTOR
register. But in for example nRF52840 using their SoftDevice, the interrupts are
forwarded in software to the application for SoftDevice to override.

```
(gdb) arm nvic 80 &__isr_vector
IRQn Prio          Handler
 -15    0 en          0002a749 Reset      -
 -14    0 en          0002a771 NMI        -
 -13    0 en          0002bc55 HardFault  HardFault_Handler
 -12    0 en          0002bc5d MemManage
 -11    0 en          0002bc59 BusFault
 -10    0 en          0002bc61 UsageFault
  -5   80 en          00027201 SVC        SVC_Handler
  -2   e0 en          00027231 PendSV     PendSV_Handler
   0   80 en          00027715 POWER_CLOCK_IRQHandler
   2   40 en          0002c409 UARTE0_UART0_IRQHandler
  11    0 en          0002a783 -
  17   c0 en pend     0002bd4d RTC1_IRQHandler
  21   40 en          0002bd55 SWI1_EGU1_IRQHandler
  22   c0 en          000279e9 SWI2_EGU2_IRQHandler
  23   a0 en          0002c035 SWI3_EGU3_IRQHandler
  25   80 en          0002a783 -
  32   20 en          0002a783 -
```

To use an SVD file from cmsis-svd package database, use:

This loads in the device description under a local name, in this case `nrf` for
faster access in upcoming commands

```
(gdb) arm loaddb nrf52 Nordic nrf52.svd
(gdb) arm loadfile stm32f7x7 /path/to/my/stm32f7x7.svd
(gdb) arm list nrf
FICR       @ 0x10000000
UICR       @ 0x10001000
BPROT      @ 0x40000000
POWER      @ 0x40000000
...
```

It is possible to inspect the values of the registers on the target
```
(gdb) arm inspect nrf52840 NVMC
NVMC.READY                       = 00000001
    READY                          .......1 - Ready
NVMC.READYNEXT                   = 00000001
    READYNEXT                      .......1 - Ready
NVMC.CONFIG                      = 00000000
    WEN                            .......0 - Ren
NVMC.ERASEPAGE                   = 00000000
NVMC.ERASEPCR1                   = 00000000
NVMC.ERASEALL                    = 00000000
    ERASEALL                       .......0 - NoOperation
NVMC.ERASEPCR0                   = 00000000
NVMC.ERASEUICR                   = 00000000
    ERASEUICR                      .......0 - NoOperation
NVMC.ERASEPAGEPARTIAL            = 00000000
NVMC.ERASEPAGEPARTIALCFG         = 0000000a
    DURATION                       ......0a - 0a
NVMC.ICACHECNF                   = 00000001
    CACHEEN                        .......1 - Enabled
    CACHEPROFEN                    .....0.. - Disabled
NVMC.IHIT                        = 00000000
NVMC.IMISS                       = 00000000
```