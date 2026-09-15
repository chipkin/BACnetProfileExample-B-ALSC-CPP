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

Part of the CAS BACnet Stack **BACnet profile example series** - one repository
per BACnet device profile. This example claims **only** B-ALSC.

> **Versions:** this document describes **example v1.0.0**, built and verified
> against **CAS BACnet Stack 6.0.21 (`6.x` @ `abd4cee1`)**, linked as a static
> library, at **Protocol_Revision 24**, with the vendored `common/` helper at
> **v2.5.0**. Running the example prints all three - if what it prints disagrees
> with this line, trust the program and check `CHANGELOG.md`.

> **⚠ CRITICAL, VERIFIED LIMITATION: Life Safety Point/Zone objects (Amber,
> Azure) currently cannot serve almost any property over the wire.** This is a
> **stack-source gap, inherited unchanged from
> [B-LSC](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP)** (this
> repository's seed), re-verified against this repository's own build:
> `Object_List` correctly lists both objects and `Object_Type` reads back, but
> `Object_Name`, `Present_Value`, `Out_Of_Service`, and every other property
> answer `Error(...): object: unknown-object` - and the same WriteProperty of
> `Present_Value` this README uses as the alarm/fault demo trigger fails the
> same way. **Root cause is in the stack, not this example's code** - see
> **[TODO.md #0](TODO.md)** for the full trace and the filed stack issue
> ([chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036)).
> Because the same alarm path feeds this repository's own new **Event Log**
> feature, that gap has one direct consequence here too - see
> **[TODO.md #3](TODO.md)** - though the Event Log's own properties
> (existence, `Log_Enable`, `ReadRange`, `Record_Count`) are independently
> verified working. This example implements every B-ALSC capability the
> standard CAS BACnet Stack's customer-facing API exposes, and the items above
> are the dominant things it cannot do - full list in **[TODO.md](TODO.md)**
> and "What this example does NOT do yet" below.

This example is seeded from
[B-LSC (Life Safety Controller)](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP)
and adds an **Event Log** object (F-EVENTLOG, this series' canonical source for
that feature) plus a **Schedule + Calendar** pair (F-SCHED-I, copied
byte-for-byte from
[B-AAC](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP)'s canonical
pattern). Everything else - the three read-only inputs, three commandable
outputs, the two life-safety objects, and Notification Class 1 "Crimson" - is
unchanged from B-LSC.

## What is a B-ALSC (Advanced Life Safety Controller) profile?

A **device profile** (ANSI/ASHRAE 135, Annex L) lists the capabilities a class of
device must support. A **B-ALSC** (Annex L.5) is a B-LSC fire/smoke panel-style
controller that additionally **logs events** (Event Log, cl. 12.27) and runs
**internal scheduling** (Schedule + Calendar, cl. 12.24/12.23). (New to BACnet?
See Chipkin's [What is BACnet?](https://docs.chipkin.com/protocols/bacnet/) guide.)

**What the profile requires** (and where this example stands):

| Requirement | BIBB | This example |
|---|---|:--:|
| ReadProperty | DS-RP-B | ✅ |
| ReadPropertyMultiple | DS-RPM-B | ✅ |
| WriteProperty | DS-WP-B | ✅ |
| WritePropertyMultiple | DS-WPM-B | ✅ |
| SubscribeCOV | DS-COV-B | ✅ |
| Generate life-safety event notifications | AE-LS-B | ✅ (intrinsic ChangeOfLifeSafety + fault; alarming itself is blocked by issue #2036 - see the callout above) |
| Accept AcknowledgeAlarm | AE-ACK-B | ✅ |
| Answer GetEventInformation | AE-INFO-B | ✅ |
| Event Log + ReadRange | AE-EL-I-B | ✅ (Event Log 1 "Beige"; own properties verified, alarm-capture demo blocked by the same issue) |
| Internal scheduling | SCHED-I-B | ✅ (Schedule 1 "Saffron" + Calendar 1 "Cream") |
| Who-Is/I-Am (answer + initiate), Who-Has/I-Have | DM-DDB-A,B, DM-DOB-B | ✅ |
| DeviceCommunicationControl | DM-DCC-B | ✅ |
| Time synchronisation | DM-TS-B / DM-UTC-B | ✅ |
| ReinitializeDevice | DM-RD-B | ✅ (cold/warm start) |

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
affect the profile table above.

## F-EVENTLOG: Event Log 1 "Beige" (this repository's new feature)

`BACnetStack_AddEventLogObject` creates a clause-12.27 Event Log whose core
properties (`Enable`, `Buffer_Size`, `Record_Count`, `Total_Record_Count`,
`Log_Buffer`, ...) are held and served **by the stack itself**, answered
before this file's own callbacks are ever consulted. `Log_Buffer` is read with
**ReadRange** (service 35) - a plain ReadProperty of it is not refused, but
per the stack's own doc comment it always answers an empty list, so use
ReadRange.

**Verified over the wire** (`bacpypes3`, against this repository's own build):
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
- which is exactly what issue #2036 blocks. See **[TODO.md #3](TODO.md)**.

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
cannot be populated through the customer API (cas-bacnet-stack issue #963 -
see `TODO.md`); `Present_Value` always answers `false` rather than evaluating
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

The three inputs and three outputs are the series' shared minimum plus F-OUTPUTS
(canonical: B-SA); **Amber, Azure and Crimson are B-LSC's life-safety
additions; Beige, Saffron and Cream are this repository's B-ALSC additions**.
Object names follow the series' colour convention (Device is always
"Rainbow").

## What this example does NOT do yet

A faithful, honest example: these details are **not** implemented, because the
standard CAS BACnet Stack does not yet expose a way to (or, for LifeSafetyOperation,
ship a build configured to). Full detail and "what it would take" is in
**[TODO.md](TODO.md)**.

- **⚠ Life Safety Point 1 (Amber) and Life Safety Zone 1 (Azure) cannot serve
  almost any property.** Inherited from B-LSC and re-verified against this
  repository's own build. `BACnetStack_AddObject` (the only customer-facing way
  to create one) never populates the stack's internal
  `BACnetStackLifeSafetyPoint`/`Zone` engine object - only
  `BACnetDBDevice::AddLifeSafetyPointObject`/`AddLifeSafetyZoneObject` do that,
  and neither is exported. See **[TODO.md #0](TODO.md)** for the full trace and
  [chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036).
- **Life Safety Zone 1 (Azure)'s `Zone_Members`** - a required (cl. 12.16)
  constructed property with no customer-facing serving path (see
  **[TODO.md #1](TODO.md)**), same as B-LSC.
- **LifeSafetyOperation is not enabled on the wire** - `STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION`
  is not part of this series' build preset (see **[TODO.md #2](TODO.md)**).
  DM-LSO-B is not itself a BIBB B-ALSC requires.
- **⚠ Event Log 1 (Beige) cannot demonstrate capturing Amber's/Azure's own
  alarm** - the SAME root cause as the Life Safety gap above, not a new one.
  Beige's own properties (existence, `Log_Enable`, `ReadRange`, `Record_Count`)
  are independently verified working. See **[TODO.md #3](TODO.md)**.

## Before you ship

This example is a tutorial, and it identifies itself as one. Everything in this
table is read by clients and shown to the operator in **every discovery tool on
the network**. Left as-is, your product appears on a real site announcing itself
as a Chipkin demo. None of it is cosmetic.

| Constant (`main.cpp`) | Ships as | Change it to |
|---|---|---|
| `VENDOR_IDENTIFIER` | `389` (Chipkin) | **Your** company's vendor ID. Assigned by ASHRAE, free: <https://bacnet.org/assigned-vendor-ids/> |
| `VENDOR_NAME` | `Chipkin Automation Systems` | Your company name - must match the vendor ID above. |
| `DEVICE_NAME` | `"Rainbow"` | Your device's `Object_Name`. **Must be unique across the BACnet internetwork** - see the note below. |
| `MODEL_NAME` | `CAS BACnet Stack Example - B-ALSC` | Your model designation - what a building operator reads to identify your device. |
| `DEVICE_DESCRIPTION` | a description of *this example* | What your device actually is. |
| `FIRMWARE_REVISION` / `APPLICATION_SOFTWARE_VERSION` | `1.0.0` | Your real versions - wire them to your build. |
| `DCC_PASSWORD` | `""` (no password) | Set your device's secret, or leave empty to accept any DeviceCommunicationControl. It crosses the wire in **plaintext** - a guard against accidents, not a security boundary. |
| Device instance | `389008` (`--deviceID` overrides) | Must be unique on the internetwork. BACnet requires this to be configurable; keep it so. |

> **`Object_Name` uniqueness is the one that will bite you.** The device instance
> is runtime-configurable via `--deviceID`, but `DEVICE_NAME` is a compile-time
> constant. Ship two units and configure their instances correctly, and **both
> still announce `Object_Name "Rainbow"`** - a spec violation, and exactly the
> uniqueness problem the code comments warn about. In a real product,
> `Object_Name` must be per-unit configurable too (serial number, DIP switches,
> a config file, or a `--deviceName` argument).

`main.cpp` marks this block with a `CHANGE ALL OF THIS BEFORE YOU SHIP` banner.

## Requires the CAS BACnet Stack (licensed product)

This example **builds against the CAS BACnet Stack, a commercial Chipkin product** -
not free or open source, no public/trial build. The stack is the **private** git
submodule `submodules/cas-bacnet-stack`; you can only fetch and build it with a CAS
BACnet Stack license. **To get the stack, contact Chipkin:**
<https://store.chipkin.com/services/stacks/bacnet-stack> or sales@chipkin.com. You
do not need a stack licence to *read* this example's own source: every file outside
submodules/ is CC0 public domain. The licence is what lets you *build* it.

## Build

This example links the CAS BACnet Stack as a prebuilt **STATIC** library. Build
the library once from the pinned submodule commit, then configure and build the
example against it:

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP.git
cd BACnetProfileExample-B-ALSC-CPP
git submodule update --init --recursive   # if not cloned with --recursive
tools/build-stack-static.sh BACnetProfileExample-B-ALSC-CPP   # from the series root; builds
                                                                # submodules/cas-bacnet-stack/bin/...
cmake -B build -S . -DCAS_BACNET_STACK_LINK=STATIC
cmake --build build --config Release
./build/BACnetExampleBALSC            # Linux/macOS
.\build\Release\BACnetExampleBALSC.exe   # Windows
```

> **The stack library build takes a few minutes** the first time - it compiles
> the entire CAS BACnet Stack (~600 source files) once, via the stack's own
> project files (`msbuild` on Windows, `make` on Linux). The example itself
> (`main.cpp` + `common/`) then builds in seconds against that library, and
> rebuilds after that are incremental.

Use `-D CAS_STACK_DIR=/path` to point at a stack elsewhere. Options: `--port <n>`
(default 47808), `--deviceID <n>` (default 389008), `--help` (show usage and exit),
`--version` (print the example, stack, and `common/` versions and exit).
Interactive keys: `h` help, `q` quit, up/down nudge Analog Input 1 (also feeds its
COV subscribers), `s` advance Schedule 1 ("Saffron") with a Weekly_Schedule
transition for right now.

### Link mode

This example links the stack through the `CASBACnetStack::Adapter` CMake target
(`submodules/cas-bacnet-stack/adapters/cpp`) in **STATIC** mode -
`-DCAS_BACNET_STACK_LINK=STATIC` links the prebuilt
`CASBACnetStack_x64_Release.lib` / `libCASBACnetStack_x64_Release.a` built by
`tools/build-stack-static.sh` above. **Application code is identical
regardless of link mode** - `main.cpp` and `common/` call `BACnetStack_AddDevice(...)`
and friends by the exact export name. Every mode requires calling
`LoadBACnetFunctions()` once at the top of `main()` before any other
`BACnetStack_*` call, which runs a version handshake; if it fails,
`CASBACnetStackAdapter_LastError()` says why and the program exits with a
message rather than crashing.

The adapter also offers a **SOURCE** mode (compiles the stack's `source/*.cpp`
straight into the executable, no library build step) - this example is built
and published in **STATIC** mode only.

## Verify

With the [CAS BACnet Explorer](https://store.chipkin.com/products/tools/cas-bacnet-explorer)
(or any client, e.g. `bacpypes3`/`BAC0`). Steps below were run against this
repository's own built binary with `bacpypes3` in this task; step 4 (the
alarm) is expected to fail per the callout above.

1. **Discover** - Who-Is → I-Am from `389008` (vendor `389`). ✅ verified (the
   device's own start-up I-Am broadcast was observed on the wire).
2. **Object model** - thirteen objects incl. Life Safety Point "Amber", Life
   Safety Zone "Azure", Notification Class "Crimson", Event Log "Beige",
   Schedule "Saffron", Calendar "Cream". ✅ verified: `Object_Type` reads back
   on Amber; `Object_Name`/`Object_Type` read back on Beige, Saffron and
   Cream; everything else on Amber/Azure does not (see below).
3. **Event Log** - `Object_Name`/`Buffer_Size`/`Record_Count`/`Total_Record_Count`
   read correctly; `Log_Enable` WriteProperty round-trips; `ReadRange` of
   `Log_Buffer` succeeds and returns a real record after toggling `Log_Enable`.
   ✅ verified.
4. **Fire a life-safety alarm** - WriteProperty Amber's `Present_Value` = `2`
   (alarm); watch the `CHANGE_OF_LIFE_SAFETY` EventNotification arrive and
   `Record_Count` on Beige advance. **Currently fails**: WriteProperty of
   `Present_Value` (and `ReadProperty` of nearly everything on Amber/Azure)
   answers `Error(...): object: unknown-object` - see [TODO.md #0](TODO.md);
   `Record_Count` on Beige correspondingly does not move. ✅ this failure mode
   itself is verified (re-confirms issue #2036 against this repository's
   build).
5. **Schedule** - press `s`, then ReadProperty Chartreuse's `Present_Value` a
   moment later; it moves to `75.0` at priority 8. `Priority_For_Writing` (8)
   and `Schedule_Default` (20.0) on Saffron verified by ReadProperty; the
   scheduled write itself (pressing `s` and observing Chartreuse move) was not
   exercised this session (flagged rather than assumed).
6. **Acknowledge / LifeSafetyOperation / COV / Device management** - not
   exercised this session beyond what B-LSC's own task already verified
   (unchanged code paths); see B-LSC's README for that verification detail.

## What's in this repository

`main.cpp` (the example), `common/` (the vendored shared helper), and
`submodules/cas-bacnet-stack/` (the CAS BACnet Stack as a private git submodule,
compiled from source). Self-contained: clone with `--recursive` and build.

## Objects and properties

<!-- OBJECTS-PROPERTIES:BEGIN (generated by tools/gen-objects-properties.py from docs/objects.json - do not edit here) -->
Every object this example creates, and every REQUIRED property of each (per ANSI/ASHRAE 135-2024 clause 12 and the stack's `docs/property-profile-reference.md`), plus the optional properties the example turns on. **Served by** says who answers a ReadProperty: the **stack** generates it, or the **app** serves it from a `GetProperty*` callback in `main.cpp`. A ⚠ row is a required property the app does not serve and the stack would fill with a default - that is a defect, not a feature.

### Analog Input 1 "Bronze" - REAL, degrees Celsius; starts at 21.5. Present_Value is DS-COV-B subscribable (BACnetStack_SetPropertySubscribable); the up/down key feeds subscribers via BACnetStack_UpdateValue

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |

### Binary Input 1 "Emerald" - starts inactive

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |

### Multi-state Input 1 "Hot Pink" - state 1 of 3: On, Off, Auto

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| State_Text *(optional, enabled)* | BACnetARRAY[N] of CharacterString | app | no |

### Analog Output 1 "Chartreuse" - F-OUTPUTS (canonical: B-SA). commandable; 16-slot Priority_Array, Relinquish_Default 20.0 C, served by GetPropertyReal. Present_Value, Priority_Array and Current_Command_Priority are resolved by the stack from the priority array. ALSO the SCHED-I-B write target - Schedule 1 (Saffron) writes it at priority 8

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalReal | stack | no |
| Relinquish_Default | Real | app | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Binary Output 1 "Fuchsia" - F-OUTPUTS. commandable; 16-slot Priority_Array, Relinquish_Default inactive, served by GetPropertyEnumerated

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalBinaryPV | stack | no |
| Relinquish_Default | BACnetBinaryPV | app | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Multi-state Output 1 "Indigo" - F-OUTPUTS. commandable; 16-slot Priority_Array, Relinquish_Default state 1 of 3, served by GetPropertyUnsignedInteger

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalUnsigned | stack | no |
| Relinquish_Default | Unsigned | app | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Life Safety Point 1 "Amber" - VERIFIED CRITICAL GAP (TODO.md #0, carried forward from BACnetProfileExample-B-LSC-CPP and re-verified against this repository's own build): almost every property on this object currently answers unknown-object over the wire, because BACnetStack_AddObject never populates the stack internal life-safety engine object (AddLifeSafetyPointObject/AddLifeSafetyZoneObject are not customer-exported) - see chipkin/cas-bacnet-stack#2036. F-LIFESAFETY / F-ALARM-LS (canonical: B-LSC). BACnetLifeSafetyState Present_Value: quiet(0)/alarm(2)/fault(3); Tracking_Value mirrors it (this example's simplification - see main.cpp file header for why it does not use the stack's internal, non-customer-exported life-safety engine). Present_Value is made WRITABLE beyond the profile's read-only column purely as this tutorial's alarm/fault trigger (mirrors B-AAC's Diamond) - and that WriteProperty is exactly what issue #2036 blocks. Mode is required-writable by the profile and accepted unconditionally (no customer-facing Accepted_Modes setter exists - see the file header); Accepted_Modes is therefore accepted at the stack's generic default. Event_State is NOT actually a stack default here - it is genuinely computed, because this example arms ChangeOfLifeSafety + fault intrinsic algorithms on Amber (SetIntrinsicChangeOfLifeSafetyAlgorithm/SetFaultLifeSafetyAlgorithm); it is marked accepted only because property-profile-reference.md's generic table does not know an algorithm was armed (same convention as B-AAC's Diamond). Present_Value is also DS-COV-B subscribable

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetLifeSafetyState | app | yes |
| Tracking_Value | BACnetLifeSafetyState | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Mode | BACnetLifeSafetyMode | app | yes |
| Accepted_Modes | BACnetLIST of BACnetLifeSafetyMode | stack default, accepted (Generic Enumerated default: `0`) | no |
| Silenced | BACnetSilencedState | app | no |
| Operation_Expected | BACnetLifeSafetyOperation | app | no |

### Life Safety Zone 1 "Azure" - VERIFIED CRITICAL GAP (TODO.md #0, carried forward from BACnetProfileExample-B-LSC-CPP and re-verified against this repository's own build): almost every property on this object currently answers unknown-object over the wire - see chipkin/cas-bacnet-stack#2036. F-LIFESAFETY / F-ALARM-LS. Event_State is genuinely computed (same as Amber's - ChangeOfLifeSafety + fault algorithms armed on Azure too), marked accepted for the same generator-limitation reason. Same shape as Amber (this example holds Azure's own independent Present_Value rather than rolling it up from Zone_Members - the stack's real zone roll-up engine is not customer-exported, see the file header). Zone_Members (cl. 12.16, required, BACnetLIST of BACnetDeviceObjectReference) has NO servable path on the customer surface: the only generic constructed-property callback, BACnetStack_RegisterCallbackGetPropertyConstructed, was moved to the test-tool DLL (CASBACnetStackDLL.h's own PR #193 review comment) and is forbidden by this series. See TODO.md and the filed stack issue - this is a real, verified gap, not a convenience shortcut

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetLifeSafetyState | app | yes |
| Tracking_Value | BACnetLifeSafetyState | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Mode | BACnetLifeSafetyMode | app | yes |
| Accepted_Modes | BACnetLIST of BACnetLifeSafetyMode | stack default, accepted (Generic Enumerated default: `0`) | no |
| Silenced | BACnetSilencedState | app | no |
| Operation_Expected | BACnetLifeSafetyOperation | app | no |
| Zone_Members | BACnetLIST of BACnetDeviceObjectReference | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Notification Class 1 "Crimson" - Priority, Ack_Required and Recipient_List are NOT stack DEFAULTS - they are genuinely populated, by BACnetStack_AddNotificationClassObject (Priority, Ack_Required) and BACnetStack_AddRecipientToNotificationClass (Recipient_List) at start-up. They are marked accepted only because property-profile-reference.md's generic per-type table does not know about this object-specific host-configuration API and so cannot credit them as stack-served. Routes Amber's and Azure's CHANGE_OF_LIFE_SAFETY / fault notifications

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Priority | BACnetARRAY[3] of Unsigned | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Ack_Required | BACnetEventTransitionBits | stack default, accepted (Generic BitString default: empty bitstring (zero bits - NOT ) | no |
| Recipient_List | BACnetLIST of BACnetDestination | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Event Log 1 "Beige" - F-EVENTLOG (canonical: this repository). Enable/Buffer_Size/Record_Count/Total_Record_Count/Log_Buffer/Status_Flags/Object_Identifier/Object_Type/Property_List are NOT stack defaults in the generic sense - they are genuinely held and served by the stack's own Event Log engine (BACnetStack_AddEventLogObject), answered from stack storage BEFORE this file's Get*/Set* callbacks are ever consulted; marked accepted only because property-profile-reference.md's generic table does not know about this object-specific engine. VERIFIED over the wire with a live bacpypes3 client against this repository's own build: Object_Name/Object_Type/Buffer_Size/Record_Count/Total_Record_Count read correctly; Enable (property id 133) round-trips a WriteProperty false->true correctly; ReadRange of Log_Buffer (service 35, RangeByPosition) succeeds and returns real BACnetLogRecords - toggling Enable was independently captured as a clause-12.27 log-status transition with no application code involved (Record_Count/Total_Record_Count moved 0->1, ReadRange returned exactly that record), proving the automatic capture hook is live in this build. NOT verified: capturing Amber's/Azure's own CHANGE_OF_LIFE_SAFETY notification - that requires Amber/Azure to actually reach alarm(2), which is blocked by the SAME root cause as the Life Safety Point/Zone gap above (issue #2036) - see TODO.md #3. BACnetStack_InsertEventLogRecord (the only app-facing way to seed a record directly) was moved to the test-tool surface in v6 and is forbidden by this series, so this example never calls it and never fakes a record. Event_State is accepted at the stack's generic default (normal) - this example does not arm intrinsic reporting on Beige itself (only on Amber/Azure), matching the doc comment on BACnetStack_AddEventLogObject: with neither an alarm engine nor a callback armed, the stack answers normal(0)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Enable | Boolean | stack default, accepted (Generic Boolean default: `false`) | yes |

### Schedule 1 "Saffron" - SCHED-I-B (identical pattern to B-AAC's canonical Saffron - this series' copy source for F-SCHED-I). Present_Value, Effective_Period, Schedule_Default, List_Of_Object_Property_References, Priority_For_Writing and Status_Flags are NOT stack DEFAULTS - they are genuinely held and served by the stack's Schedule engine (BACnetStack_AddScheduleObject plus the BACnetStack_SetSchedule*/AddSchedule* configuration calls in main.cpp); it writes Analog Output 1 (Chartreuse) Present_Value at priority 8. Present_Value, Effective_Period and Priority_For_Writing are marked accepted only because property-profile-reference.md's generic table does not know about the Schedule engine's own host-configuration API. One weekly transition (Monday 08:00) and one calendar-date exception (2026-12-25, via the inline calendar-entry form) are seeded at start-up; the 's' key (common/ 2.1.0's DemoAdvance) adds a transition for right now so the change can be observed without waiting for the wall clock. VERIFIED over the wire: Object_Name, Priority_For_Writing (8) and Schedule_Default all read back correctly

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Any | stack default, accepted (Stack-generated if commandable (resolves the priority array)) | no |
| Effective_Period | BACnetDateRange | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Schedule_Default | Any | stack | no |
| List_Of_Object_Property_References | BACnetLIST of BACnetDeviceObjectPropertyReference | stack | no |
| Priority_For_Writing | Unsigned(1..16) | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |

### Calendar 1 "Cream" - exists for SCHED-I-B completeness alongside Saffron's exception, but its Date_List cannot be populated through the customer API (cas-bacnet-stack issue #963 - no read path for a Calendar object's Date_List; the only generic constructed-property callback is test-tool-only). Present_Value therefore always answers false rather than evaluating a Date_List that is never populated - see TODO.md. VERIFIED over the wire: Object_Name and Present_Value (false) both read back correctly

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Boolean | app | no |
| Date_List | BACnetLIST of BACnetCalendarEntry | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |

### Network Port 1 "Vermilion" - BACnet/IP; Network_Type and Protocol_Level are set from BACnetStack_AddNetworkPortObject()'s arguments (IPv4, BACnet Application) at start-up, not a GetProperty callback like the object's other app-served rows; Changes_Pending is likewise computed and answered natively by the stack's Network Port object. Reliability has no fault condition this example detects, so it is accepted at the generic default (normal)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Network_Type | BACnetNetworkType | app | no |
| Protocol_Level | BACnetProtocolLevel | app | no |
| Changes_Pending | Boolean | app | no |

<!-- OBJECTS-PROPERTIES:END -->

## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
The CAS BACnet Stack supports every standardized device profile in ASHRAE 135-2024 Annex L. One example repository per profile shows how. ✅ = the required BIBB (service) is supported by the CAS BACnet Stack; the **Example** column is the state of that profile's tutorial repository.

### Controllers (Annex L.4)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-SS** Smart Sensor | [B-SS-CPP](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) ✅ | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-SA** Smart Actuator | [B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-ASC** Application Specific Controller | [B-ASC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP) ✅ · [B-ASC-Node](https://github.com/chipkin/BACnetProfileExample-B-ASC-Node) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B |
| **B-AAC** Advanced Application Controller | [B-AAC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP) ✅ | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-CRL-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |
| **B-BC** Building Controller | [B-BC-CPP](https://github.com/chipkin/BACnetProfileExample-B-BC-CPP) 📝 | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-RPM-B · ✅ DS-WP-A · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-CRL-B · ✅ SCHED-E-B · ✅ T-VMT-I-B · ✅ T-ATR-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B · ✅ DM-BR-B |

### Life safety controllers (Annex L.5)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-LSC** Life Safety Controller | [B-LSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) 📝 | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ AE-LS-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |
| **B-ALSC** Advanced Life Safety Controller | [B-ALSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP) ✅ | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ AE-LS-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |

### Access control controllers (Annex L.6)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) 🚧 | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ DS-ACUC-B · ✅ DS-ACSC-B · ✅ AE-AC-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B · ✅ DM-BR-B |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) 📝 | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-RPM-B · ✅ DS-WP-A · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-A · ✅ DS-COV-B · ✅ DS-ACAD-A · ☐ DS-ACCDI-A · ✅ DS-ACUC-B · ✅ DS-ACSC-B · ✅ AE-AC-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B · ✅ DM-BR-B |

### Lighting controllers (Annex L.11)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-LD** Lighting Device | [B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DS-LO-B / DS-BLO-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |
| **B-LS** Lighting Supervisor | [B-LS-CPP](https://github.com/chipkin/BACnetProfileExample-B-LS-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-WP-B · ✅ DS-WG-E-B · ✅ DS-ALO-A · ✅ SCHED-E-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |

### Elevator controllers (Annex L.13)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-EM** Elevator Monitor | [B-EM-CPP](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) ✅ | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-COV-B · ✅ DS-COVM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B |
| **B-EC** Elevator Controller | [B-EC-CPP](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP) 📝 | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ DS-COVM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-RD-B |
| **B-AEC** Advanced Elevator Controller | [B-AEC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AEC-CPP) 📝 | ✅ DS-RP-B · ✅ DS-RPM-B · ✅ DS-WP-B · ✅ DS-WPM-B · ✅ DS-COV-B · ✅ DS-COVM-B · ✅ AE-N-I-B · ✅ AE-ACK-B · ✅ AE-INFO-B · ✅ AE-EL-I-B · ✅ SCHED-I-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B · ✅ DM-OCD-B · ✅ DM-RD-B · ✅ DM-BR-B |

### Authentication and authorization (Annex L.14)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) 🚧 | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ AA-AS-B |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ NM-BBMDC-B |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DS-ACAD-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DS-COV-B · ✅ DS-ACCDI-B · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-A · ✅ DM-DOB-B · ☐ DM-LM-B · ✅ NM-RC-B |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) 📝 | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ GW-EO-B / GW-VN-B |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) ✅ | ✅ DS-RP-B · ✅ DS-WP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DAB-B |
| **B-SCHUB** BACnet/SC Hub | [B-SCHUB-CPP](https://github.com/chipkin/BACnetProfileExample-B-SCHUB-CPP) 📝 | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ NM-SCH-B |
| **B-GENERAL** General device (Annex L.8) | *(satisfied by every example above)* | ✅ DS-RP-B · ✅ DM-DDB-B · ✅ DM-DOB-B |

### Operator interfaces and workstations (Annex L.1–L.3, L.9–L.10, L.12) — client-side profiles

| Profile | Example | Required BIBBs (services) |
|---|---|---|
| **B-OD** Operator Display | [B-OD-CPP](https://github.com/chipkin/BACnetProfileExample-B-OD-CPP) ✅ | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-V-A · ✅ DS-M-A · ✅ AE-N-A · ✅ AE-VN-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-OWS** Operator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-V-A · ✅ DS-M-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-VM-A · ✅ AE-VN-A · ✅ SCHED-VM-A · ✅ T-V-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-MTS-A |
| **B-AWS** Advanced Operator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-AV-A · ✅ DS-AM-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-AVM-A · ✅ AE-AVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A · ✅ DM-DDA-A · ✅ NM-CC-A · ✅ AR-AVM-A |
| **B-XAWS** Extended Advanced Operator Workstation | planned | ✅ union of B-AWS + B-AACWS + B-ALWS + B-AEWS |
| **B-LSAP** Life Safety Annunciator Panel | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-LSV-A · ✅ AE-N-A · ✅ AE-LS-A · ✅ AE-ACK-A · ✅ AE-LSVN-A |
| **B-LSWS** Life Safety Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-LSV-A · ✅ DS-LSM-A · ✅ AE-N-A · ✅ AE-LS-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-LSVM-A · ✅ AE-LSAVN-A · ✅ AE-ELV-A · ✅ SCHED-VM-A · ✅ T-V-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |
| **B-ALSWS** Advanced Life Safety Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-LSAV-A · ✅ DS-LSAM-A · ✅ AE-N-A · ✅ AE-LS-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-LSAVM-A · ✅ AE-LSAVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A · ✅ AR-AVM-A |
| **B-ACSD** Access Control Security Display | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-ACV-A · ✅ DS-ACM-A · ✅ AE-N-A · ✅ AE-AC-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-ACAVN-A · ✅ AE-ELV-A · ✅ SCHED-VM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-MTS-A |
| **B-ACWS** Access Control Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-ACAV-A · ✅ DS-ACM-A · ✅ DS-ACUC-A · ✅ AE-N-A · ✅ AE-AC-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-ACVM-A · ✅ AE-ACAVN-A · ✅ AE-ELV-A · ✅ SCHED-VM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |
| **B-AACWS** Advanced Access Control Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-ACAV-A · ✅ DS-ACAM-A · ✅ DS-ACUC-A · ✅ DS-ACSC-A · ✅ AE-N-A · ✅ AE-AC-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-ACAVM-A · ✅ AE-ACAVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A · ✅ AR-AVM-A |
| **B-LOD** Lighting Operator Display | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-LV-A · ✅ DS-WG-A · ✅ DS-ALO-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-ALWS** Advanced Lighting Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-LAV-A · ✅ DS-LAM-A · ✅ DS-WG-A · ✅ DS-ALO-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-AVM-A · ✅ AE-AVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |
| **B-LCS** Lighting Control Station | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-LO-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |
| **B-ALCS** Advanced Lighting Control Station | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-WG-A · ✅ DS-ALO-A · ✅ SCHED-E-B · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B · ✅ DM-DCC-B · ✅ DM-TS-B / DM-UTC-B |
| **B-ED** Elevator Display | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-WP-A · ✅ DS-EV-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-EVN-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-DOB-B |
| **B-EWS** Elevator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-COVM-A · ✅ DS-EV-A · ✅ DS-EM-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-EVM-A · ✅ AE-EAVN-A · ✅ SCHED-VM-A · ✅ T-V-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A |
| **B-AEWS** Advanced Elevator Workstation | planned | ✅ DS-RP-A · ✅ DS-RP-B · ✅ DS-RPM-A · ✅ DS-WP-A · ✅ DS-WPM-A · ✅ DS-COVM-A · ✅ DS-EAV-A · ✅ DS-EAM-A · ✅ AE-N-A · ✅ AE-ACK-A · ✅ AE-AS-A · ✅ AE-EAVM-A · ✅ AE-EAVN-A · ✅ AE-ELVM-A · ✅ SCHED-AVM-A · ✅ T-AVM-A · ✅ DM-DDB-A · ✅ DM-DDB-B · ✅ DM-ANM-A · ✅ DM-ADM-A · ✅ DM-DOB-B · ✅ DM-DCC-A · ✅ DM-MTS-A · ✅ DM-OCD-A · ✅ DM-RD-A · ✅ DM-BR-A |

Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
<!-- PROFILE-TABLE:END -->

## Footprint

Release-build sizes and start-up timing, from the latest tagged release's CI
run (`metrics-windows.json` / `metrics-linux.json`), both built with
`CAS_BACNET_STACK_LINK=STATIC`:

<!-- METRICS -->
| Platform | Binary | Size | SHA-256 (prefix) | Start-up to `ready` | Stack commit | Link mode | Compiler |
|---|---|---|---|---|---|---|---|
| windows-2022 | `BACnetExampleBALSC.exe` | 3,429,888 bytes | `22a050d7f30b1e62` | 246 ms | `abd4cee1` (6.0.21) | STATIC | Visual Studio 17 2022 |
| ubuntu-latest | `BACnetExampleBALSC` | 59,504 bytes | `f6032465d99585a6` | 109 ms | `abd4cee1` (6.0.21) | STATIC | `/usr/bin/c++` |

## References

- **ANSI/ASHRAE 135** - object model (Clause 12), alarming/events (Clause 13),
  services (Clause 16), device profiles (Annex L).
- **CAS BACnet Stack** - <https://store.chipkin.com/services/stacks/bacnet-stack>.
- **B-LSC example** (the sibling this builds on) -
  <https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP>.
- **B-AAC example** (Schedule/Calendar pattern source) -
  <https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP>.
- **[TODO.md](TODO.md)** - what is not implemented and why.
- **[CHANGELOG.md](CHANGELOG.md)**, **[AGENTS.md](AGENTS.md)**,
  **[`common/README.md`](common/README.md)**.

## Use this in your own project

Self-contained: clone (with the submodule) and build, then copy what you need. The
example source is **CC0-1.0** (public domain). The CAS BACnet Stack is a separate,
commercially licensed product not covered by CC0.
