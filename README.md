arm-gdb
=======

Tools for debugging ARM registers within GDB

Run
---

Start GDB and run
```
python import arm_gdb
```

Exmaples
---

Dump of ARM System Control Block, with bitmask descriptions
```
(gdb) arm scb
ACTLR  = 00000000                     // Auxiliary Control Register
CPUID  = 410fc241                     // CPUID Base Register
         00000001 -    1 - Revision
         0000c240 -  c24 - PartNo
         000f0000 -    f - Constant
         41000000 -   41 - Implementer
ICSR   = 04421003                     // Interrupt Control and State Register
         00000003 -   03 - VECTACTIVE
         00021000 -   21 - VECTPENDING
         00400000 -    1 - ISRPENDING
         04000000 -    1 - PENDSTSET
VTOR   = 00000000                     // Vector Table Offset Register
AIRCR  = fa050000                     // Application Interrupt and Reset Control Register
         fa050000 - fa05 - VECTKEY
SCR    = 00000000                     // System Control Register
CCR    = 00000200                     // Configuration and Control Register
         00000200 -    1 - STKALIGN
SHPR1  = 00000000                     // System Handler Priority Register 1
SHPR2  = 80000000                     // System Handler Priority Register 2
         80000000 -   80 - PRI_11 - SVCall
SHPR3  = e0000000                     // System Handler Priority Register 3
         e0000000 -   e0 - PRI_15 - SysTick
SHCRS  = 00000800                     // System Handler Control and State Register
         00000800 -    1 - SYSTICKACT
CFSR   = 00040000                     // Configurable Fault Status Register
MMFSR  =       00                     // MemManage Fault Status Register
MMFAR  = e000edf8                     // MemManage Fault Address Register
BFSR   =       00                     // BusFault Status Register
BFAR   = e000edf8                     // BusFault Address Register
UFSR   =     0004                     // UsageFault Status Register
             0004 -    1 - INVPC
HFSR   = 40000000                     // HardFault Status Register
         40000000 -    1 - FORCED
AFSR   = 00000000                     // Auxiliary Fault Status Register
```

Dump of ARM SysTick, with bitmask descriptions
```
(gdb) arm systick
SYST_CSR   = 00000004                     // SysTick Control and Status Register
             00000004 -    1 - CLKSOURCE
SYST_RVR   = 00000000                     // SysTick Reload Value Register
SYST_CVR   = 00000000                     // SysTick Current Value Register
SYST_CALIB = c0000000                     // SysTick Calibration Value Register
             40000000 -    1 - SKEW
             80000000 -    1 - NOREF
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