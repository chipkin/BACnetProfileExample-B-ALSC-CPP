# BACnet B-ALSC (Advanced Life Safety Controller) - C++ example

A tutorial example of the BACnet **B-ALSC (Advanced Life Safety Controller)**
device profile in C++, using the
[CAS BACnet Stack](https://store.chipkin.com/services/stacks/bacnet-stack).

**What it does** - the profile's function, 135-2024 Annex L.5.1: "A B-ALSC
device performs life safety alarm detection and control. It supports life
safety objects and limited modification of its alarm and event reporting,
including event distribution by another device. Also, the device supports
scheduling of internal values and event logging." It is
[B-LSC](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) plus those
three things:

1. **Smoke.** The detector (Life Safety Point 1 "Amber") sees smoke:
   `Tracking_Value` goes to `alarm`, `Present_Value` **latches** `alarm`, and
   its zone (Life Safety Zone 1 "Azure") follows.
2. **The alarm goes to the recipients** in Notification Class 1 "Crimson"'s
   `Recipient_List` - at start-up the operator workstation, **Device 389108**,
   as a **ConfirmedEventNotification** (`CHANGE_OF_LIFE_SAFETY`, to
   `LIFE_SAFETY_ALARM`). **Another device may rewrite that list** - event
   distribution by another device - and the next alarm follows it.
3. **Every alarm is logged** in Event Log 1 "Beige" - whether or not its
   recipient could be reached - and read back with **ReadRange**.
4. **The operator handles it**: `LifeSafetyOperation` **SILENCE**,
   **AcknowledgeAlarm** (every recipient gets the `ACK_NOTIFICATION`), and -
   once the smoke has gone - **RESET**, which notifies the return to normal.
5. **Schedule 1 "Saffron"** writes Analog Output 1 "Chartreuse" by date and
   time - 75.0 from Monday 08:00, 5.0 on every date in Calendar 1 "Cream"
   (December 25), 20.0 otherwise - against the device clock a
   **TimeSynchronization** sets.

**Failure Modes** the Wire Tests show:

- **RESET while the detector still sees smoke is refused** - `OBJECT` /
  `INVALID_OPERATION_IN_THIS_STATE` (cl. 13.13.1.3.1, 13.13.2) - and the
  alarm stays latched. So is a RESET of an object that is not latched.
- **A detector fault** gives `Reliability` `MULTI_STATE_FAULT`, the `FAULT`
  flag and event state, notified to the workstation; `RESET_FAULT` cannot
  clear it, repairing the detector does.
- **An alarm nobody acknowledges stays listed** by GetEventInformation.
- **The recipient cannot be reached** (it never announced itself): the alarm
  is still in the Event Log and in GetEventInformation.

> **The smoke detector is Simulation.** There is no detector loop card here:
> what the detector reads (`quiet`, `smoke`, `fault`) is a variable in
> `main.cpp` (section 1b, "SIMULATION: the smoke detector"). Only the Wire
> Tests move it, through a **loopback-only test control channel**
> ([`simulation/SimulationControl.h`](simulation/SimulationControl.h)) that is
> off unless the environment variable `BALSC_SIMULATION_CONTROL_PORT` names a
> UDP port - it is not a command-line option, and nothing on the BACnet
> network can reach it. A real product deletes `simulation/` and feeds
> `ApplyDetectorReading()` from its detector inputs. Everything a BACnet
> client sees is real BACnet behaviour of this example and the CAS BACnet
> Stack.

**[Download a prebuilt binary](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP/releases)**
(Windows and Linux x64) - or build it yourself, see [Build](#build) below.

- **[TUTORIAL.md](TUTORIAL.md)** - how to extend this example and how to review
  it for conformance. Read it when you start turning this into your own device.
- **[docs/PICS.md](docs/PICS.md)** - the Protocol Implementation Conformance
  Statement: every object, every property, and who answers it.
- **[tests/](tests/README.md)** - the Wire Tests that prove the scenario and
  the Failure Modes, from outside the example, over BACnet/IP.

> **Versions:** this document describes **example v1.3.0**, built and verified
> against **CAS BACnet Stack 6.0.23 (`6.x` @ `69b6249f`)**, at
> **Protocol_Revision 30**, with the vendored `common/` helper at **v3.5.0**
> and `wiretest/` at **v0.7.0**. Running the example prints the first three -
> if what it prints disagrees with this line, trust the program and check
> `CHANGELOG.md`.

> **Known gaps at stack `6.x` @ `69b6249f`** (details in [TODO.md](TODO.md);
> the Wire Tests report each as a `[KNOWN GAP]`):
>
> - **Zone_Members is always empty.** Azure rolls up Amber, but the customer
>   interface has no way to list Amber in `Zone_Members`
>   ([chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036)).
> - **Event Log 1 starts disabled.** `Enable` starts FALSE and the customer
>   interface cannot set it at creation
>   ([chipkin/cas-bacnet-stack#3301](https://github.com/chipkin/cas-bacnet-stack/issues/3301)),
>   so an operator writes it TRUE before anything is logged.

## What this example supports

### BIBBs (BACnet Interoperability Building Blocks)

The B-ALSC column of the Annex L.5 table - every row is required:

| BIBB | Description | Supported |
|---|---|:--:|
| DS-RP-B | Data Sharing - ReadProperty - B | ✅ |
| DS-RPM-B | Data Sharing - ReadPropertyMultiple - B | ✅ |
| DS-WP-B | Data Sharing - WriteProperty - B | ✅ |
| DS-WPM-B | Data Sharing - WritePropertyMultiple - B | ✅ |
| DS-COV-B | Data Sharing - COV - B | ✅ |
| AE-LS-B | Life-safety notifications; silence and reset operations | ✅ Wire Tested |
| AE-ACK-B | Accept AcknowledgeAlarm | ✅ Wire Tested |
| AE-INFO-B | Answer GetEventInformation | ✅ Wire Tested |
| AE-EL-I-B | Event Log + ReadRange | ✅ Wire Tested (Event Log 1 "Beige"; `Enable` must be written TRUE first - see above) |
| SCHED-I-B | Internal scheduling | ✅ Wire Tested (Schedule 1 "Saffron" + Calendar 1 "Cream") |
| DM-DDB-A, DM-DDB-B | Who-Is/I-Am (answer + initiate) | ✅ |
| DM-DOB-B | Who-Has/I-Have | ✅ |
| DM-DCC-B | DeviceCommunicationControl | ✅ |
| DM-TS-B / DM-UTC-B | Time synchronisation (sets the device clock the Schedule runs on) | ✅ Wire Tested |
| DM-RD-B | ReinitializeDevice | ✅ (cold/warm start) |

Every required property of every object, and who answers it, is in
[docs/PICS.md](docs/PICS.md).

## The device this example creates

```
Device 389008  "Chipkin Example B-ALSC"   (Vendor 389 - Chipkin Automation Systems)
    ├── Analog Input  1       "Bronze"      sensor (REAL, deg C); COV-subscribable; Out_Of_Service writable
    ├── Binary Input  1       "Emerald"     read-only sensor (active/inactive)
    ├── Multi-State Input 1   "Hot Pink"    read-only sensor (state 1..3)
    ├── Analog Output 1       "Chartreuse"  writable, commandable (REAL); Schedule-driven at priority 8
    ├── Binary Output 1       "Fuchsia"     writable, commandable (0/1)
    ├── Multi-State Output 1  "Indigo"      writable, commandable (state 1..3)
    ├── Life Safety Point 1   "Amber"       the smoke detector (SIMULATION input); latches alarm; COV-subscribable
    ├── Life Safety Zone 1    "Azure"       the detector's zone; rolls Amber up (Zone_Members empty - see above)
    ├── Notification Class 1  "Crimson"     alarms, confirmed, to Device 389108 at start-up; Recipient_List writable
    ├── Event Log 1           "Beige"       logs every alarm; Log_Buffer via ReadRange; Enable writable
    ├── Schedule 1            "Saffron"     drives Chartreuse: Monday 08:00 75.0, Cream's dates 5.0, else 20.0
    ├── Calendar 1            "Cream"       stack-held; Date_List = December 25, every year
    └── Network Port 1        "Vermilion"   the BACnet/IP port (required)
```

Amber, Azure and Crimson are B-LSC's life-safety objects; Beige, Saffron and
Cream are B-ALSC's additions. `main.cpp` is B-LSC's plus those additions, so
the two files diff cleanly.

### Services (executed / B-side)

| Service | Notes |
|---------|-------|
| ReadProperty / ReadPropertyMultiple | DS-RP-B / DS-RPM-B. |
| WriteProperty / WritePropertyMultiple | The commandable outputs, Amber's/Azure's `Mode`, Crimson's `Recipient_List`, Beige's `Enable`. Amber's/Azure's `Present_Value` is read-only (Table 12-18): `write-access-denied`. |
| SubscribeCOV | Bronze's and Amber's `Present_Value` (DS-COV-B); Bronze's `COV_Increment` is 1.0. |
| ConfirmedEventNotification | Initiated to the `Recipient_List`, retried up to `Number_Of_APDU_Retries` (3) times (AE-LS-B). |
| LifeSafetyOperation | Silence / unsilence / reset (AE-LS-B). Compiled in by `CMakeLists.txt` - see [Build](#build). |
| AcknowledgeAlarm | The stack sends the `ACK_NOTIFICATION` (AE-ACK-B). |
| GetEventInformation | Active and unacknowledged events (AE-INFO-B). |
| ReadRange | Event Log 1's `Log_Buffer` (AE-EL-I-B); a ReadProperty of it is refused (cl. 12.27.13). |
| Who-Is / I-Am, Who-Has / I-Have | DM-DDB-A,B / DM-DOB-B. |
| DeviceCommunicationControl | Enable / disable-initiation, password-gated (DM-DCC-B). |
| ReinitializeDevice | Cold/warm start; SimpleACKs then actually restarts (DM-RD-B). |
| TimeSynchronization / UTCTimeSynchronization | Sets the device clock (`Local_Date` / `Local_Time`), which Saffron and Cream run on (DM-TS-B / DM-UTC-B). |

## Requires the CAS BACnet Stack (licensed product)

This example **builds against the CAS BACnet Stack, which is a commercial Chipkin
product** - it is not free or open source, and there is no public/trial build.
The stack is referenced here as the **private** git submodule
`submodules/cas-bacnet-stack`; you can only fetch and build it once you have a CAS
BACnet Stack license and access to that repository.

**To get the CAS BACnet Stack (and access to build this example), contact
Chipkin:** <https://store.chipkin.com/services/stacks/bacnet-stack> or
sales@chipkin.com.

You do not need a stack licence to *read* this example, or to run a
[prebuilt release binary](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP/releases).
The licence is what lets you *build* it - that is the part the stack submodule
gates.

## What's in this repository

This is a **self-contained** project. It ships:

- `main.cpp` - the example device. Section 1b is the smoke-detector
  **Simulation**.
- `simulation/` - the Wire Tests' loopback-only test control channel to the
  simulated detector (**Simulation**, off unless
  `BALSC_SIMULATION_CONTROL_PORT` is set; a real product deletes it).
- `common/` - the shared helper (UDP, callbacks, CLI, keyboard) vendored in.
- `CMakeLists.txt` - the build, the same on Windows, Linux, and macOS. It also
  turns on the stack's LifeSafetyOperation service (see [Build](#build)).
- `docs/PICS.md` - the conformance statement.
- `TODO.md` - the known gaps, with their evidence.
- `tests/` - the Wire Tests (see [Wire Tests](#wire-tests)), and `wiretest/`, the
  series' shared Python harness they are written against (vendored, like `common/`).
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack as a git submodule**
  (private; requires a license - see above). Its sources are compiled into the
  executable, so there is no library or DLL to build, ship, or install.

## Prerequisites

- A C++17 compiler (MSVC, GCC, or Clang).
- CMake >= 3.15.
- Git (to fetch the stack submodule).
- Python 3 (standard library only) to run the Wire Tests.

### Windows

- **C++ compiler** - install
  [Visual Studio Community](https://visualstudio.microsoft.com/downloads/)
  (free) and select the **"Desktop development with C++"** workload.
- **CMake** - from <https://cmake.org/download/>, or `winget install Kitware.CMake`.

### Linux / macOS

- Debian/Ubuntu: `sudo apt install build-essential cmake git`
- macOS: `xcode-select --install` and `brew install cmake`

## Build

CMake only, and the same two commands on every platform:

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP.git
cd BACnetProfileExample-B-ALSC-CPP

cmake -B build -S .
cmake --build build --config Release
```

Already cloned without `--recursive`? Run `git submodule update --init --recursive`
first - the build needs the stack submodule.

> **The first build takes a few minutes** - it compiles the entire CAS BACnet
> Stack (~600 source files) into the executable. Rebuilds after that are
> incremental and take seconds.

If your CAS BACnet Stack lives somewhere other than the bundled submodule, point
CMake at it: `cmake -B build -S . -D CAS_STACK_DIR=/path/to/cas-bacnet-stack`.

**LifeSafetyOperation needs a stack build option.** AE-LS-B executes
LifeSafetyOperation, and the stack compiles that service only when
`STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION` is defined - its documented public
toggle (`CASBACnetStackOptions.h`); the default `STACK_OPTION_TARGET_FULL`
preset leaves it off. In SOURCE mode `CMakeLists.txt` defines it for you. If
you link a prebuilt stack instead (`-D CAS_BACNET_STACK_LINK=STATIC` or `DLL`),
build that library with the option, e.g. on Windows from the examples-series
folder:

```bash
CL=-DSTACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION tools/build-stack-static.sh BACnetProfileExample-B-ALSC-CPP
```

(`-D`, not `/D`: Git Bash rewrites `/D...` into a path. If the library was
already built, rebuild it from clean - msbuild does not notice a changed `CL`.)
A stack built without it makes the example stop at start-up with
`Error: Failed to enable the LifeSafetyOperation (AE-LS-B) ...` rather than
advertise a service it cannot execute.

## Run

```bash
# Linux / macOS
./build/BACnetExampleBALSC

# Windows
.\build\Release\BACnetExampleBALSC.exe
```

Options: `--port <n>` (default 47808), `--deviceID <n>` (default 389008),
`--deviceName <text>` (default `Chipkin Example B-ALSC`; the Device object's
`Object_Name`, 1..255 bytes, no control characters; it must be unique across the
BACnet internetwork, so give every unit its own - BACnet requires it to be
configurable, like the instance; an invalid value prints a warning and keeps the
default), `--xml` (off by default; print every received and sent BACnet message
as an indented XML block instead of a one-line summary - very verbose, for
protocol debugging), `--help` (show usage and exit), `--version` (print the example, stack, and
`common/` versions and exit).

Expected output (captured from a real build, here with `--port 48068`):

```
BACnet B-ALSC (Advanced Life Safety Controller) Example - C++ v1.3.0
CAS BACnet Stack version: 6.0.23.0
Common helper (common/) version: 3.5.0
FYI: Listening for BACnet/IP on UDP port 48068 (Network Port 1).
TX 21 bytes to 192.168.3.255:48068 (broadcast) (Network Port 1) - Unconfirmed: I-Am
TX 8 bytes to 192.168.3.255:48068 (broadcast) (Network Port 1) - Unconfirmed: Who-Is
FYI: Device 389008 ("Chipkin Example B-ALSC") ready. Vendor ID 389. Press 'h' for help.
RX 21 bytes from 192.168.3.64:48068 (Network Port 1) - Unconfirmed: I-Am
WriteProperty: Analog Output 1 (Chartreuse) <- 20.00 @ priority 8
TX 20 bytes to 192.168.3.255:48068 (broadcast) (Network Port 1) - Unconfirmed: Who-Is DNET=65535
```

The `WriteProperty: Analog Output 1 (Chartreuse) <- 20.00 @ priority 8` line is
Schedule 1 writing its `Schedule_Default` on its first evaluation. The first two
`TX` lines are the start-up I-Am and Who-Is, to the **local
subnet broadcast** address (computed from the Network Port's interface), not
the global `255.255.255.255`. The `RX ... I-Am` is the device hearing its own
broadcast. The `Who-Is DNET=65535` is the stack looking for **Device 389108**,
the operator workstation in Crimson's start-up `Recipient_List`: until a device
with that instance answers (or announces itself with an I-Am) alarms for it
have nowhere to go - they are still logged.

The device listens on UDP **47808** (BACnet/IP). Allow that port through your
firewall. To use a different port, pass `--port` (see above).

> **A wall of red `Error:` lines at start-up is expected and is not your bug** -
> it is the stack's own debug logging. [TUTORIAL.md](TUTORIAL.md#troubleshooting)
> explains it.

### Interactive commands

While the example runs, these keys are available:

| Key | Action |
|-----|--------|
| `h` | Show the version information and this command list. |
| `q` | Quit. |
| up arrow | Increase Analog Input 1 (`Bronze`) by 1.1 (feeds its COV subscribers while it is in service). |
| down arrow | Decrease Analog Input 1 (`Bronze`) by 1.1. |
| `s` | Add a `Weekly_Schedule` transition to Schedule 1 (`Saffron`) for right now (device clock). |

There is no detector key. The **Simulation**'s smoke detector is moved through
the loopback test control channel, which is off unless you start the example
with `BALSC_SIMULATION_CONTROL_PORT` set (Linux:
`BALSC_SIMULATION_CONTROL_PORT=47809 ./build/BACnetExampleBALSC`). Then send it
one plain-text UDP datagram per command, from the same host:

| Command | Reply | The detector |
|---------|-------|--------------|
| `detector smoke` | `ok` | sees smoke - Amber and Azure go to alarm and latch |
| `detector quiet` | `ok` | the smoke has cleared / the head is back on its base |
| `detector fault` | `ok` | its head is pulled off its base |
| `detector` | `detector <smoke\|quiet\|fault>` | (just reports) |

For example, on Linux: `echo -n "detector smoke" | nc -u -w1 127.0.0.1 47809`.

## Verify

Use a BACnet client such as the
[**CAS BACnet Explorer**](https://store.chipkin.com/products/tools/cas-bacnet-explorer):

1. **Discover** - send a **Who-Is**. The device replies with **I-Am** from
   instance **389008** (vendor **389**).
2. **Browse the object model** - thirteen objects besides the Device. Every
   property each object lists reads as a value, except Event Log 1's
   `Log_Buffer`, which is read with ReadRange (the Wire Tests check this).
3. **Life-safety alarming** - write your client into Crimson's
   `Recipient_List` (or give it device instance 389108), write Beige's `Enable`
   TRUE, start the example with the test control channel on, and send
   `detector smoke`. Your client receives a `CHANGE_OF_LIFE_SAFETY`
   ConfirmedEventNotification for Amber and for Azure; ReadRange of Beige's
   `Log_Buffer` shows both. Silence with LifeSafetyOperation `silence`,
   acknowledge, send `detector quiet`, and `reset`; try `reset` first and see
   it refused.
4. **Schedule** - TimeSynchronization to a Monday after 08:00: Saffron and
   Chartreuse read 75.0; to December 25: 5.0 (Cream is TRUE); to a Monday
   before 08:00: 20.0.

For a full property-by-property review against the conformance statement, see
[TUTORIAL.md](TUTORIAL.md).

## Wire Tests

Automated, from outside the example: Python 3 (standard library only) starts
the example with its test control channel on, plays the **operator
workstation** (Device 389108, the Peer) over BACnet/IP, and plays the physical
world through the control channel. Each check fails when the function it
proves is removed - every one was mutation-verified (see `CHANGELOG.md`).

| Script | What it proves |
|--------|----------------|
| `discovery_test.py` | Who-Is, `Object_List`, a ReadProperty of every listed property; `Log_Buffer` refused; `Database_Revision` (14); a SubscribeCOV with an 8-hour lifetime. |
| `configuration_test.py` | The command line: `--deviceID` and `--deviceName` configure the Device's instance and Object_Name (Who-Is, ReadProperty, Who-Has; a WriteProperty of the name is refused; the name's limits), and `--help` lists exactly the options the example reads. |
| `life_safety_test.py` | The life-safety scenario (as B-LSC's): smoke -> latched alarm -> notifications to Device 389108 (not to a stranger) -> RESET refused while smoke is present -> SILENCE -> AcknowledgeAlarm + ACK_NOTIFICATION -> the latch holds -> RESET -> return to normal; an unacknowledged alarm stays listed. Zone_Members: `[KNOWN GAP]`. |
| `fault_test.py` | A detector fault -> Reliability `MULTI_STATE_FAULT`, FAULT, to-fault notification; `RESET_FAULT` refused; repaired. |
| `event_log_test.py` | With `Enable` FALSE nothing is logged; written TRUE, the alarm is logged (ReadRange) even though the recipient is unreachable, and GetEventInformation still lists it. Enable at start-up: `[KNOWN GAP]` (#3301). |
| `distribution_test.py` | A second workstation rewrites `Recipient_List`; the next alarm reaches it and not the bound Device 389108. |
| `schedule_test.py` | TimeSynchronization moves the device clock; Cream, Saffron and Chartreuse (`Priority_Array[8]`) follow: 5.0 / 75.0 / 20.0. |

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBALSC          # Linux/macOS
python tests\run_wire_tests.py --exe build\Release\BACnetExampleBALSC.exe   # Windows
```

It ends with `ALL WIRE TESTS PASSED` (exit 0). The example uses `--port` and
`--port` + 1 (the control channel). [tests/README.md](tests/README.md) says
what each check proves.

## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
There is one example repository per standardized device profile in ASHRAE 135-2024 Annex L. An example marked ⛔ is blocked: the stack cannot yet perform that profile's function through its customer interface, and the example's README says what it does today. Pick the profile your device claims, then the language you build in. "Ask" means the example hasn't been built yet for that language - [contact Chipkin](https://store.chipkin.com/contact-us) if you need one.

### Controllers (Annex L.4)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-SS** Smart Sensor | [B-SS-CPP](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) | [B-SS-Node](https://github.com/chipkin/BACnetProfileExample-B-SS-Node) | [B-SS-CS](https://github.com/chipkin/BACnetProfileExample-B-SS-CS) | [B-SS-Rust](https://github.com/chipkin/BACnetProfileExample-B-SS-Rust) | [B-SS-Python](https://github.com/chipkin/BACnetProfileExample-B-SS-Python) | [B-SS-Go](https://github.com/chipkin/BACnetProfileExample-B-SS-Go) |
| **B-SA** Smart Actuator | [B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ASC** Application Specific Controller | [B-ASC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP) | [B-ASC-Node](https://github.com/chipkin/BACnetProfileExample-B-ASC-Node) | Ask | Ask | Ask | Ask |
| **B-AAC** Advanced Application Controller | [B-AAC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-BC** Building Controller | [B-BC-CPP](https://github.com/chipkin/BACnetProfileExample-B-BC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Life safety controllers (Annex L.5)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LSC** Life Safety Controller | [B-LSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) 🚧 | Ask | Ask | Ask | Ask | Ask |
| **B-ALSC** Advanced Life Safety Controller | [B-ALSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Access control controllers (Annex L.6)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) ⛔ blocked on [stack #2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150), [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) | Ask | Ask | Ask | Ask | Ask |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) ⛔ blocked on [stack #2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150), [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) | Ask | Ask | Ask | Ask | Ask |

### Lighting controllers (Annex L.11)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LD** Lighting Device | [B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-LS** Lighting Supervisor | [B-LS-CPP](https://github.com/chipkin/BACnetProfileExample-B-LS-CPP) | Ask | Ask | Ask | Ask | Ask |

### Elevator controllers (Annex L.13)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-EM** Elevator Monitor | [B-EM-CPP](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-EC** Elevator Controller | [B-EC-CPP](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-AEC** Advanced Elevator Controller | [B-AEC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AEC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Authentication and authorization (Annex L.14)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) ⛔ blocked on [stack #2043](https://github.com/chipkin/cas-bacnet-stack/issues/2043) | Ask | Ask | Ask | Ask | Ask |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) ⛔ blocked on [stack #3934](https://github.com/chipkin/cas-bacnet-stack/issues/3934) | Ask | Ask | Ask | Ask | Ask |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) ⛔ blocked on [stack #2032](https://github.com/chipkin/cas-bacnet-stack/issues/2032) | Ask | Ask | Ask | Ask | Ask |
| **B-SCHUB** BACnet/SC Hub | [B-SCHUB-CPP](https://github.com/chipkin/BACnetProfileExample-B-SCHUB-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GENERAL** General device (Annex L.8) | *(satisfied by every example above)* | — | — | — | — | — |

### Operator interfaces and workstations (Annex L.1–L.3, L.9–L.10, L.12)

Client-side profiles.

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-OD** Operator Display | [B-OD-CPP](https://github.com/chipkin/BACnetProfileExample-B-OD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-OWS** Operator Workstation | planned | — | — | — | — | — |
| **B-AWS** Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-XAWS** Extended Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-LSAP** Life Safety Annunciator Panel | planned | — | — | — | — | — |
| **B-LSWS** Life Safety Workstation | planned | — | — | — | — | — |
| **B-ALSWS** Advanced Life Safety Workstation | planned | — | — | — | — | — |
| **B-ACSD** Access Control Security Display | planned | — | — | — | — | — |
| **B-ACWS** Access Control Workstation | planned | — | — | — | — | — |
| **B-AACWS** Advanced Access Control Workstation | planned | — | — | — | — | — |
| **B-LOD** Lighting Operator Display | planned | — | — | — | — | — |
| **B-ALWS** Advanced Lighting Workstation | planned | — | — | — | — | — |
| **B-LCS** Lighting Control Station | planned | — | — | — | — | — |
| **B-ALCS** Advanced Lighting Control Station | planned | — | — | — | — | — |
| **B-ED** Elevator Display | planned | — | — | — | — | — |
| **B-EWS** Elevator Workstation | planned | — | — | — | — | — |
| **B-AEWS** Advanced Elevator Workstation | planned | — | — | — | — | — |

🚧 = in progress. ⛔ = Blocked Example (blocked on the named stack gap). "Ask" = not yet built for that language; contact Chipkin if you need it. Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
<!-- PROFILE-TABLE:END -->

## References

- **ANSI/ASHRAE 135** - object model (Clause 12), alarming/events (Clause 13),
  services (Clause 16), device profiles (Annex L). Purchase / preview via the
  [ASHRAE store](https://www.ashrae.org/technical-resources/standards-and-guidelines).
- **What is BACnet?** - Chipkin's introduction:
  <https://docs.chipkin.com/protocols/bacnet/>.
- **CAS BACnet Stack** - product page and documentation:
  <https://store.chipkin.com/services/stacks/bacnet-stack>.
- **CAS BACnet Explorer** - client for testing this device:
  <https://store.chipkin.com/products/tools/cas-bacnet-explorer>.
- **B-LSC example** (the sibling this builds on) -
  <https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP>.
- **B-AAC example** (Schedule/Calendar pattern source) -
  <https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP>.
- **Shared helper used by this example** - [`common/README.md`](common/README.md).

See also [TUTORIAL.md](TUTORIAL.md), [docs/PICS.md](docs/PICS.md),
[TODO.md](TODO.md), [CHANGELOG.md](CHANGELOG.md), and [AGENTS.md](AGENTS.md).
