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

Usage
-----

Use `help arm` command, or individual subcommands, i.e. `help arm scb`

```
(gdb) help arm
Tools for debugging ARM Cortex-M - series CPUs

List of arm subcommands:

arm fpu -- Dump of ARM Cortex-M FPU - SCB registers for the FP extension
arm inspect -- Dump register values from device peripheral
arm list -- List peripherals and registers from device
arm loaddb -- Load an SVD file from resitry
arm loadfile -- Load an SVD file from file
arm nvic -- Print current status of NVIC
arm scb -- Dump of ARM Cortex-M SCB - System Control Block
arm systick -- Dump of ARM Cortex-M SysTick block

Type "help arm" followed by arm subcommand name for full documentation.
Type "apropos word" to search for commands related to "word".
Type "apropos -v word" for full documentation of commands related to "word".
Command name abbreviations are allowed if unambiguous.
```

System Control Block
--------------------

```
(gdb) help arm scb
Dump of ARM Cortex-M SCB - System Control Block

Usage: arm scb [/habf]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values
Modifier /b prints bitmasks in binary instead of hex
Modifier /f force printing fields from all Cortex-M models
```

Dump of ARM System Control Block, with bitmask descriptions
```
(gdb) arm scb /h
SCB for model M4

SCB registers:
CPUID                            = 410fc241                   // CPUID Base Register
    Implementer                    41...... - ARM             // Implementer code assigned by Arm
    Architecture                   ...f.... - f               // constant - 1111
    PartNo                         ....c24. - Cortex-M4
    Revision                       .......1 - 1
ICSR                             = 00000000                   // Interrupt Control and State Register
VTOR                             = 00000000                   // Vector Table Offset Register
AIRCR                            = fa050000                   // Application Interrupt and Reset Control Register
    ENDIANNESS                     ....0... - Little Endian
SCR                              = 00000000                   // System Control Register
CCR                              = 00000200                   // Configuration and Control Register
SHPR1                            = 00000000                   // System Handler Priority Register 1
SHPR2                            = 80000000                   // System Handler Priority Register 2
    PRI_11 - SVCall                80...... - 80              // Priority of system handler 11, SVCall.
SHPR3                            = 00e00000                   // System Handler Priority Register 3
    PRI_14 - PendSV                ..e0.... - e0              // Priority of system handler 14, PendSV.
SHCSR                            = 00070000                   // System Handler Control and State Register
    USGFAULTENA                    ...4.... - 1               // Indicates if UsageFault is enabled.
    BUSFAULTENA                    ...2.... - 1               // Indicates if BusFault is enabled.
    MEMFAULTENA                    ...1.... - 1               // Indicates if MemFault is enabled.
CFSR                             = 00000000                   // Configurable Fault Status Register
    MMFSR                          ......00 - 00              // MemManage Fault Status Register
    BFSR                           ....00.. - 00              // BusFault Status Register
    UFSR                           0000.... - 0000            // UsageFault Status Register
HFSR                             = 00000000                   // HardFault Status Register
DFSR                             = 00000001                   // Debug Fault Status Register
    HALTED                         .......1 - Halt request debug event // Indicates a debug event generated by either C_HALT, C_STEP or DEMCR.MON_STEP
MMFAR                            = e000edf8                   // MemManage Fault Address Register
BFAR                             = e000edf8                   // BusFault Address Register
AFSR                             = 00000000                   // Auxiliary Fault Status Register
CPACR                            = 00f00000                   // Coprocessor Access Control Register

AUX registers:
ICTR                             = 00000001                   // Interrupt Controller Type Register
    INTLINESNUM                    .......1 - 64 vectors      // The total number of interrupt lines supported, as 32*(1+N)
ACTLR - M4                       = 00000000                   // Auxiliary Control Register - Cortex M4
```

SysTick
-------

```
(gdb) help arm systick
Dump of ARM Cortex-M SysTick block

Usage: arm systick [/hab]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values
Modifier /b prints bitmasks in binary instead of hex
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

Print out all fields, even those with default values:
```
(gdb) arm systick /ab
SYST_CSR                         = 00000000000000000000000000000100
    ENABLE                         ...............................0 - 0
    TICKINT                        ..............................0. - 0
    CLKSOURCE                      .............................1.. - 1
    COUNTFLAG                      ...............0................ - 0
SYST_RVR                         = 00000000000000000000000000000000
    RELOAD                         ........000000000000000000000000 - 000000
SYST_CVR                         = 00000000000000000000000000000000
    CURRENT                        ........000000000000000000000000 - 000000
SYST_CALIB                       = 11000000000000000000000000000000
    TENMS                          .......0000000000000000000000000 - 0000000
    SKEW                           .1.............................. - 1
    NOREF                          1............................... - 1
```

FPU
---

```
(gdb) help arm fpu
Dump of ARM Cortex-M FPU - SCB registers for the FP extension

Usage: arm fpu [/hab]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values
Modifier /b prints bitmasks in binary instead of hex
```

```
(gdb) arm fpu/ab
SCB FP registers:
FPCCR                            = 11000000000000000000000000000000
    ASPEN                          1............................... - 1
    LSPEN                          .1.............................. - 1
    MONRDY                         .......................0........ - 0
    BFRDY                          .........................0...... - 0
    MMRDY                          ..........................0..... - 0
    HFRDY                          ...........................0.... - 0
    THREAD                         ............................0... - 0
    USER                           ..............................0. - 0
    LSPACT                         ...............................0 - 0
FPCAR                            = 00000000000000000000000000000000
    FPCAR                          ..0000000000000000000000000000.. - 0000000
FPDSCR                           = 00000000000000000000000000000000
    AHP                            .....0.......................... - 0
    DN                             ......0......................... - 0
    FZ                             .......0........................ - 0
    RMode                          ........00...................... - 0
MVFR0                            = 00010000000100010000000000100001
    FP rounding modes              0001............................ - All rounding modes supported.
    Short vectors                  ....0000........................ - Not supported
    Square root                    ........0001.................... - Supported
    Divide                         ............0001................ - Supported
    FP exception trapping          ................0000............ - Not supported
    Double-precision               ....................0000........ - Not supported
    Single-precision               ........................0010.... - Supported.
    A_SIMD registers               ............................0001 - Supported, 16 x 64-bit registers.
MVFR1                            = 00010001000000000000000000010001
    FP fused MAC                   0001............................ - Supported
    FP HPFP                        ....0001........................ - Supported half-single
    D_NaN mode                     ........................0001.... - Supported
    FtZ mode                       ............................0001 - Hardware supports full denormalized number arithmetic.
MVFR2                            = 00000000000000000000000000000000
    VFP_Misc                       ........................0000.... - No support for miscellaneous features.
```


NVIC - Nested Vectored Interrupt Controller
-------------------------------------------

Dump of NVIC list, listing all enabled interrupt handlers, in a redirected
interrupt vector

```
(gdb) help arm nvic
Print current status of NVIC

Usage: arm nvic [/a] [<ISR vector address>]

Modifier /a lists all interrupt vectors, not only enabled
    <ISR vector address> - optional. Specifies base address of ISR vector.
                           If not specified, it will be resolved via SCB->VTOR,
                           which is valid in most cases.

Examples:
    arm nvic /a            - list all ISRs from -15 to to maximum
    arm nvic &__isr_vector - Custom ISR vector, useful when proxying
                            interrupts via another system, like the
                            softdevice on nRF52
```

Default, it checks for functions in the active interrupt vector given VTOR
register. But in for example nRF52840 using their SoftDevice, the interrupts are
forwarded in software to the application for SoftDevice to override.

```
(gdb) arm nvic &__isr_vector
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

MPU - Memory Protection Unit
----------------------------

Readout for the registers in the memory protection unit on ARMv8-M devices.

```
(gdb) help arm mpu
Dump of ARM Cortex-M MPU - Memory Protection Unit registers

Usage: arm mpu [/habf]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values and disabled regions
Modifier /b prints bitmasks in binary instead of hex
Modifier /f force printing fields from all Cortex-M models
```

```
(gdb) arm mpu
MPU for Cortex-M33 - ARMv8-M

MPU common registers:

MPU_TYPE                         = 00001000 
    DREGION                        ....10.. - 10             
    SEPARATE                       .......0 - 0              
MPU_CTRL                         = 00000000 
    PRIVDEFENA                     .......0 - 0              
    HFNMIENA                       .......0 - 0              
    ENABLE                         .......0 - 0              
MPU_RNR                          = 0000000f 
    REGION                         ......0f - 0f             
MPU_MAIR0                        = 00000000 
    Outer 0                        ......0. - Device Memory  
    Device 0                       .......0 - Device-nGnRnE. 
    Outer 1                        ....0... - Device Memory  
    Device 1                       .....0.. - Device-nGnRnE. 
    Outer 2                        ..0..... - Device Memory  
    Device 2                       ...0.... - Device-nGnRnE. 
    Outer 3                        0....... - Device Memory  
    Device 3                       .0...... - Device-nGnRnE. 
MPU_MAIR1                        = 00000000 
    Outer 4                        ......0. - Device Memory  
    Device 4                       .......0 - Device-nGnRnE. 
    Outer 6                        ..0..... - Device Memory  
    Device 6                       ...0.... - Device-nGnRnE. 
    Outer 5                        ....0... - Device Memory  
    Device 5                       .....0.. - Device-nGnRnE. 
    Outer 7                        0....... - Device Memory  
    Device 7                       .0...... - Device-nGnRnE. 

MPU registers for region 0:

MPU_RBAR                         = 00000000 
    BASE                           0000000. - 00000000       
    SH                             ......00 - Non-shareable. 
    AP                             .......0 - Read/write by privileged code only.
    XN                             .......0 - Execution only permitted if read permitted
MPU_RLAR                         = 00000000 
    LIMIT                          0000000. - 00000000       
    PXN                            ......0. - Execution only permitted if read permitted.
    AttrIndx                       .......0 - 0              
    EN                             .......0 - Region disabled.

MPU registers for region 1:
```

SVD - Implementation specific peripherals
-----------------------------------------

```
(gdb) help arm inspect
Dump register values from device peripheral

Usage: arm inspect [/hab] <device> <peripheral>

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values
Modifier /b prints bitmasks in binary instead of hex

    <device>     - Name of loaded device. See `help arm loadfile`
    <peripheral> - Name of peripheral

Exmaple: arm inspect nrf52840 UARTE0
```

```
(gdb) help arm loaddb
Load an SVD file from resitry

Usage: arm loaddb <device> <vendor> <filename>

    <device>    - Name to refer to the device in commands like `arm inspect`
    <vendor>    - Device vendor
    <filename>  - SVD file within registry

Load file from cmsis-svd package registry. Many common devices are available. If
not available, you can load a custom svd file using `arm loadfile`

This command can preferrably be added to .gdbinit for easy access of devices
```

```
(gdb) help arm loadfile
Load an SVD file from file

Usage: arm loadfile <device> <filename>

    <device>    - Name to refer to the device in commands like `arm inspect`
    <filename>  - SVD file to load

This command can preferrably be added to .gdbinit for easy access of devices
```

```
(gdb) help arm list
List peripherals and registers from device

Usage: arm list

Lists loaded devices

Usage: arm list <device>

List peripherals from a device

Usage: arm list <device> <peripheral>

List registers from a peripheral

Examples:
    arm list
    arm list nrf52840
    arm list nrf52840 UARTE0
```

To use an SVD file from cmsis-svd package database, first load an SVD file:
```
(gdb) arm loadfile stm32f7x7 /path/to/my/stm32f7x7.svd
```

To list peripherals in the loaded module, use:
```
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
