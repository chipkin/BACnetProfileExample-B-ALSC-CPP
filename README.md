# BACnet B-ALSC (Advanced Life Safety Controller) - C++ example

A tutorial example showing how to implement **as much of the BACnet B-ALSC
(Advanced Life Safety Controller)** device profile as the
[CAS BACnet Stack](https://store.chipkin.com/services/stacks/bacnet-stack)
supports today, in C++. B-ALSC is **B-LSC plus an Event Log and internal
scheduling** - it answers **ReadProperty / ReadPropertyMultiple**, accepts
**WriteProperty / WritePropertyMultiple**, accepts **SubscribeCOV**, generates
**intrinsic life-safety alarms** (`CHANGE_OF_LIFE_SAFETY` EventNotifications),
accepts **AcknowledgeAlarm** and **GetEventInformation**, implements (but -
see below - cannot currently enable on the wire) a **LifeSafetyOperation**
responder, maintains an **Event Log** (readable via ReadRange), runs an
**internal Schedule + Calendar**, synchronises its clock, and handles
**DeviceCommunicationControl** and **ReinitializeDevice**.

**[Download a prebuilt binary](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP/releases)**
(Windows and Linux x64) - or build it yourself, see [Build](#build) below.

- **[TUTORIAL.md](TUTORIAL.md)** - how to extend this example and how to review
  it for conformance, including the Life Safety Point/Zone gap in detail. Read
  it when you start turning this into your own device.
- **[docs/PICS.md](docs/PICS.md)** - the Protocol Implementation Conformance
  Statement: every object, every property, and who answers it.

> **Versions:** this document describes **example v1.0.0**, built and verified
> against **CAS BACnet Stack 6.0.21 (`6.x` @ `abd4cee1`)**, at
> **Protocol_Revision 24**, with the vendored `common/` helper at **v2.5.0**.
> Running the example prints all three - if what it prints disagrees with this
> line, trust the program and check `CHANGELOG.md`.

> **⚠ CRITICAL, VERIFIED LIMITATION: Life Safety Point/Zone objects (Amber,
> Azure) currently cannot serve almost any property over the wire.** This is a
> **stack-source gap, inherited unchanged from
> [B-LSC](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP)** (this
> repository's seed): `Object_List` correctly lists both objects and
> `Object_Type` reads back, but `Object_Name`, `Present_Value`,
> `Out_Of_Service`, and every other property answer
> `Error(...): object: unknown-object` - and the same WriteProperty of
> `Present_Value` this README uses as the alarm/fault demo trigger fails the
> same way. **Root cause is in the stack, not this example's code** - see
> [TUTORIAL.md](TUTORIAL.md#the-life-safety-pointzone-gap-issue-2036) and
> [TODO.md #0](TODO.md) for the full trace and the filed stack issue
> ([chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036)).
> Event Log 1 "Beige"'s alarm-capture demo is blocked for the same reason (see
> [TODO.md #3](TODO.md)); Beige's own properties are independently verified
> working. Full list of what is and isn't implemented is in
> [TODO.md](TODO.md).

This example is seeded from
[B-LSC (Life Safety Controller)](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP)
and adds an **Event Log** object (F-EVENTLOG, this series' canonical source for
that feature) plus a **Schedule + Calendar** pair (F-SCHED-I, copied
byte-for-byte from
[B-AAC](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP)'s canonical
pattern). Everything else - the three read-only inputs, three commandable
outputs, the two life-safety objects, and Notification Class 1 "Crimson" - is
unchanged from B-LSC.

## What this example supports

### BIBBs (BACnet Interoperability Building Blocks)

| BIBB | Description | Supported |
|---|---|:--:|
| DS-RP-B | Data Sharing - ReadProperty - B | ✅ |
| DS-RPM-B | Data Sharing - ReadPropertyMultiple - B | ✅ |
| DS-WP-B | Data Sharing - WriteProperty - B | ✅ |
| DS-WPM-B | Data Sharing - WritePropertyMultiple - B | ✅ |
| DS-COV-B | Data Sharing - COV - B | ✅ |
| AE-LS-B | Generate life-safety event notifications | ✅ (intrinsic ChangeOfLifeSafety + fault; alarming itself is blocked by issue #2036 - see the callout above) |
| AE-ACK-B | Accept AcknowledgeAlarm | ✅ |
| AE-INFO-B | Answer GetEventInformation | ✅ |
| AE-EL-I-B | Event Log + ReadRange | ✅ (Event Log 1 "Beige"; own properties verified, alarm-capture demo blocked by the same issue) |
| SCHED-I-B | Internal scheduling | ✅ (Schedule 1 "Saffron" + Calendar 1 "Cream") |
| DM-DDB-A, DM-DDB-B | Who-Is/I-Am (answer + initiate) | ✅ |
| DM-DOB-B | Who-Has/I-Have | ✅ |
| DM-DCC-B | DeviceCommunicationControl | ✅ |
| DM-TS-B / DM-UTC-B | Time synchronisation | ✅ |
| DM-RD-B | ReinitializeDevice | ✅ (cold/warm start) |

`DM-LSO-B` (LifeSafetyOperation) is implemented in this example's code but not
currently enabled on the wire (see "What this example does NOT do yet" below);
it is not itself a BIBB the B-ALSC profile requires.

Every required property of every object, and who answers it, is in
[docs/PICS.md](docs/PICS.md).

## Intrinsic life-safety alarming (F-ALARM-LS / F-LIFESAFETY - inherited from B-LSC)

An **intrinsic** alarm is generated by the object itself, from an algorithm the
stack runs, with no external Event Enrollment. This example arms **Life Safety
Point 1 "Amber"** and **Life Safety Zone 1 "Azure"** with a **ChangeOfLifeSafety**
algorithm (`alarm(2)` drives the object to `LIFE_SAFETY_ALARM`) and a **fault**
algorithm (`fault(3)` drives it to `FAULT`). On each transition the stack sends an
**EventNotification** to the recipients of **Notification Class 1 "Crimson"**.

Try it: `WriteProperty` Amber's `Present_Value` to `2` (alarm) - the device prints
the write, `Event_State` becomes `life-safety-alarm`, and an
`UnconfirmedEventNotification` goes out to the recipient. Write `0` (quiet) to
return to normal. By default the recipient is the **local subnet broadcast** (so
any client sees the alarm); point it at a specific client in `main.cpp`.
**As shipped, this WriteProperty itself currently fails - see the ⚠ callout
above and [TODO.md #0](TODO.md) before trying this.**

**LifeSafetyOperation.** A client sends `silence` / `unsilence` (whole,
audible-only, or visual-only) or `reset` / `reset-alarm` / `reset-fault` -
`BACnetStack_RegisterCallbackLifeSafetyOperation` delivers it to this example's
`LifeSafetyOperation()`, which updates `Silenced` and (for a RESET) `Present_Value`
for Amber, Azure, or both. **The service is implemented in this example's code
but not currently enabled on the wire** - see "What this example does NOT do
yet" below; DM-LSO-B is not itself a BIBB B-ALSC requires, so this does not
affect the BIBB table above.

## F-EVENTLOG: Event Log 1 "Beige" (this repository's new feature)

`BACnetStack_AddEventLogObject` creates a clause-12.27 Event Log whose core
properties (`Enable`, `Buffer_Size`, `Record_Count`, `Total_Record_Count`,
`Log_Buffer`, ...) are held and served **by the stack itself**, answered
before this file's own callbacks are ever consulted. `Log_Buffer` is read with
**ReadRange** (service 35) - a plain ReadProperty of it is not refused, but
per the stack's own doc comment it always answers an empty list, so use
ReadRange.

**Verified over the wire** (a real BACnet client, against this repository's own build):
`Object_Name`/`Object_Type`/`Buffer_Size`/`Record_Count`/`Total_Record_Count`
all read correctly; `Enable` (`Log_Enable`) round-trips a `WriteProperty`
`false`→`true`; `ReadRange` of `Log_Buffer` (RangeByPosition) succeeds. The
capture hook is real, not just documented: toggling `Enable` (a
clause-12.27-mandated log-status transition) was captured automatically -
`Record_Count`/`Total_Record_Count` moved `0`→`1` and `ReadRange` returned
exactly that record, with **no application code involved**.

**Not verified: capturing Amber's/Azure's own alarm.** Per
`BACnetStack_AddEventLogObject`'s doc comment, `Log_Buffer` "normally
accumulate[s] from received event notifications" - an automatic capture, not
an application call (`BACnetStack_InsertEventLogRecord`, the only app-facing
way to insert a record directly, was moved to the test-tool surface in v6 and
is forbidden by this series, so this example never calls it and never fakes a
record). Demonstrating that requires Amber/Azure to actually reach `alarm(2)`
- which is exactly what issue #2036 blocks. See [TODO.md #3](TODO.md).

## F-SCHED-I: Schedule 1 "Saffron" + Calendar 1 "Cream" (copied from B-AAC)

Identical, byte-for-byte pattern to
[B-AAC](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP)'s canonical
Schedule/Calendar - this series' copy source for F-SCHED-I. Saffron writes
**Analog Output 1 "Chartreuse"** `Present_Value` at priority 8 whenever a
`Weekly_Schedule` or `Exception_Schedule` entry is active; `Schedule_Default`
(20.0) applies the rest of the time. One weekly transition (Monday 08:00) and
one calendar-date exception (2026-12-25, via the inline calendar-entry form -
see the Calendar note below) are seeded at start-up; the **`s`** key adds a
`Weekly_Schedule` transition for right now so the change can be observed
without waiting for the wall clock.

**Calendar 1 "Cream"** exists for SCHED-I-B completeness, but its `Date_List`
cannot be populated through the customer API
([cas-bacnet-stack#963](https://github.com/chipkin/cas-bacnet-stack/issues/963)
- see `TODO.md`); `Present_Value` always answers `false` rather than evaluating
a `Date_List` that is never populated. **Verified over the wire:**
`Object_Name`, `Priority_For_Writing` (8), and `Schedule_Default` all read
back correctly on Saffron; `Object_Name` and `Present_Value` (`false`) on
Cream.

## DS-COV-B

**Analog Input 1 "Bronze"** and **Life Safety Point 1 "Amber"** `Present_Value`
are COV-subscribable (`BACnetStack_SetPropertySubscribable`); subscription limits
are set with `SetCOVSettings`/`SetMaxActiveCOVSubscriptions`. A subscriber is
notified only when the application calls `BACnetStack_UpdateValue` for the
changed property - the up/down key (Bronze) and a `Present_Value` WriteProperty
(Amber) both already do this (the latter currently blocked - see above).

## F-REINIT (DM-RD-B)

`ReinitializeDevice` accepts `COLDSTART`/`WARMSTART`, returns a `SimpleACK`, and
performs the actual restart from the main loop one second later (after the ACK has
had time to reach the wire) - see `ReinitializeDevice()` and the deferred-restart
block in `main()`. Unchanged from B-LSC, this series' canonical F-REINIT copy
source.

## The device this example creates

```
Device 389008  "Rainbow"   (Vendor 389 - Chipkin Automation Systems)
    ├── Analog Input  1       "Bronze"      read-only sensor (REAL, deg C); COV-subscribable
    ├── Binary Input  1       "Emerald"     read-only sensor (active/inactive)
    ├── Multi-State Input 1   "Hot Pink"    read-only sensor (state 1..3)
    ├── Analog Output 1       "Chartreuse"  writable, commandable (REAL); Schedule-driven
    ├── Binary Output 1       "Fuchsia"     writable, commandable (0/1)
    ├── Multi-State Output 1  "Indigo"      writable, commandable (state 1..3)
    ├── Life Safety Point 1   "Amber"       writable; intrinsic ChangeOfLifeSafety + fault ALARM; COV-subscribable
    ├── Life Safety Zone 1    "Azure"       writable; intrinsic ChangeOfLifeSafety + fault ALARM
    ├── Notification Class 1  "Crimson"     routes Amber's/Azure's alarms to recipients
    ├── Event Log 1           "Beige"       Log_Buffer via ReadRange; Log_Enable writable
    ├── Schedule 1             "Saffron"     drives Chartreuse on a weekly + exception basis
    ├── Calendar 1             "Cream"       Date_List not evaluable (see TODO.md)
    └── Network Port 1        "Vermilion"   the BACnet/IP port (required)
```

Amber, Azure and Crimson are B-LSC's life-safety additions; Beige, Saffron and
Cream are this repository's B-ALSC additions. Object names follow the series'
colour convention (Device is always "Rainbow").

## What this example does NOT do yet

A faithful, honest example: these details are **not** implemented, because the
standard CAS BACnet Stack does not yet expose a way to (or, for
LifeSafetyOperation, ship a build configured to). Full detail and "what it
would take" is in [TODO.md](TODO.md).

- **⚠ Life Safety Point 1 (Amber) and Life Safety Zone 1 (Azure) cannot serve
  almost any property.** See [TODO.md #0](TODO.md) and
  [chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036).
- **Life Safety Zone 1 (Azure)'s `Zone_Members`** - a required (cl. 12.16)
  constructed property with no customer-facing serving path. See
  [TODO.md #1](TODO.md).
- **LifeSafetyOperation is not enabled on the wire** -
  `STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION` is not part of this series'
  build preset. See [TODO.md #2](TODO.md).
- **⚠ Event Log 1 (Beige) cannot demonstrate capturing Amber's/Azure's own
  alarm** - the SAME root cause as the Life Safety gap above, not a new one.
  See [TODO.md #3](TODO.md).

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

- `main.cpp` - the example device.
- `common/` - the shared helper (UDP, callbacks, CLI, keyboard) vendored in.
- `CMakeLists.txt` - the build, the same on Windows, Linux, and macOS.
- `docs/PICS.md` - the conformance statement.
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack as a git submodule**
  (private; requires a license - see above). Its sources are compiled into the
  executable, so there is no library or DLL to build, ship, or install.

## Prerequisites

- A C++17 compiler (MSVC, GCC, or Clang).
- CMake >= 3.15.
- Git (to fetch the stack submodule).

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

## Run

```bash
# Linux / macOS
./build/BACnetExampleBALSC

# Windows
.\build\Release\BACnetExampleBALSC.exe
```

Options: `--port <n>` (default 47808), `--deviceID <n>` (default 389008),
`--help` (show usage and exit), `--version` (print the example, stack, and
`common/` versions and exit).

Expected output:

```
BACnet B-ALSC (Advanced Life Safety Controller) Example - C++ v1.0.0
CAS BACnet Stack version: 6.0.21.0
Common helper (common/) version: 2.5.0
FYI: Listening for BACnet/IP on UDP port 47808 (Network Port 1).
TX 21 bytes to 192.168.3.255:47808 (broadcast) (Network Port 1)
FYI: Device 389008 ("Rainbow") ready. Vendor ID 389. Press 'h' for help.
```

The `TX` line is the start-up I-Am the device broadcasts to announce itself. It
goes to the **local subnet broadcast** address (here `192.168.3.255`, computed
from the Network Port's interface), not the global `255.255.255.255`. As clients
talk to the device you'll see `RX ... bytes from ...` and `TX ... bytes to ...`
lines showing the traffic.

The device listens on UDP **47808** (BACnet/IP). Allow that port through your
firewall. To use a different port, pass `--port` (see above).

> **A wall of red `Error:` lines at start-up is expected and is not your bug** -
> it is the stack's own debug logging. [TUTORIAL.md](TUTORIAL.md#troubleshooting)
> explains it, along with the `LifeSafetyOperation() ... not compiled` line.

### Interactive commands

While the example runs, these keys are available:

| Key | Action |
|-----|--------|
| `h` | Show the version information and this command list. |
| `q` | Quit. |
| up arrow | Increase Analog Input 1 (`Bronze`) by 1.1 (feeds its COV subscribers). |
| down arrow | Decrease Analog Input 1 (`Bronze`) by 1.1. |
| `s` | Advance Schedule 1 (`Saffron`) with a `Weekly_Schedule` transition for right now. |

## Verify

Use a BACnet client such as the
[**CAS BACnet Explorer**](https://store.chipkin.com/products/tools/cas-bacnet-explorer):

1. **Discover** - send a **Who-Is**. The device replies with **I-Am** from
   instance **389008** (vendor **389**). It also broadcasts an I-Am at start-up.
2. **Browse the object model** - thirteen objects, including Life Safety Point
   "Amber", Life Safety Zone "Azure", Notification Class "Crimson", Event Log
   "Beige", Schedule "Saffron", and Calendar "Cream". Reading the Device's
   `Object_List` returns all thirteen.
3. **Read a sensor and a commandable output** - ReadProperty Analog Input `1`
   -> `Present_Value` returns `21.5`. WriteProperty Analog Output `1`
   (`Chartreuse`) at a priority, re-read it, then write `NULL` to relinquish
   and confirm it falls back to `Relinquish_Default`.
4. **Event Log** - `Object_Name`/`Buffer_Size`/`Record_Count`/`Total_Record_Count`
   read correctly; `Log_Enable` WriteProperty round-trips; `ReadRange` of
   `Log_Buffer` succeeds and returns a real record after toggling `Log_Enable`.
5. **Fire a life-safety alarm** - WriteProperty Amber's `Present_Value` = `2`
   (alarm); expect this to **currently fail** with `unknown-object` - see the
   ⚠ callout above and [TODO.md #0](TODO.md).
6. **Schedule** - press `s`, then ReadProperty Chartreuse's `Present_Value` a
   moment later; it moves to the demo value at priority 8.

For a full property-by-property review against the conformance statement, see
[TUTORIAL.md](TUTORIAL.md).


## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
The CAS BACnet Stack supports every standardized device profile in ASHRAE 135-2024 Annex L, and there is one example repository per profile. Pick the profile your device claims, then the language you build in. "Ask" means the example hasn't been built yet for that language - [contact Chipkin](https://store.chipkin.com/contact-us) if you need one.

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
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) | Ask | Ask | Ask | Ask | Ask |

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
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) | Ask | Ask | Ask | Ask | Ask |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) | Ask | Ask | Ask | Ask | Ask |
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

🚧 = in progress. "Ask" = not yet built for that language; contact Chipkin if you need it. Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
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
