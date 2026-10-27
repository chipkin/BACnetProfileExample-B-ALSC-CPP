# Tutorial - extending and reviewing the B-ALSC example

[README.md](README.md) says what this example *is*. This document is the *how*:
how to extend it into your own device, who serves which property, how to review
the result for conformance, and what goes wrong when you get it subtly right.

Read this once before you start changing `main.cpp`. The most expensive mistake
in this example is silent, and the section it lives in is
[Add a second analog input](#add-a-second-analog-input). Before touching Life
Safety Point or Zone, read the
[Life Safety Point/Zone section](#life-safety-pointzone-at-this-stack-pin-issue-2036):
their state is this file's, not the stack's.

- [Extending the example](#extending-the-example)
- [Life Safety Point/Zone at this Stack Pin (issue #2036)](#life-safety-pointzone-at-this-stack-pin-issue-2036)
- [What each object type needs you to serve](#what-each-object-type-needs-you-to-serve)
- [Who serves what: the application or the stack?](#who-serves-what-the-application-or-the-stack)
- [Reviewing your device](#reviewing-your-device)
- [Troubleshooting](#troubleshooting)

## Extending the example

The example is intentionally as small as B-ALSC allows so it's easy to change.

**Change a sensor's value or name** - edit the constants / callbacks in
`main.cpp` (e.g. the initial value of `g_analogInput1Value`, or the `"Bronze"`
string in `GetPropertyCharString`).

**Change the device identity before you ship** - vendor ID, vendor name, model
name, description, firmware revision and device name are all in the
`CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of `main.cpp`, with a
per-field note on each saying what to change it to. That block is the
authoritative checklist; it is in the source rather than here so it cannot be
skipped by someone who only reads the code.

**Wire in a real detector** - the smoke detector is **Simulation** (`main.cpp`
section 1b). Everything it does goes through `ApplyDetectorReading(reading)`:
call it with `LIFE_SAFETY_STATE_QUIET`, `_ALARM` or `_FAULT` whenever your
detector loop reports a change, from the main loop. Then delete `simulation/`,
the `SimulationControl::` calls in `main()`, `HandleSimulationCommand()` and
`SIMULATION_SOURCES` in `CMakeLists.txt`.

**Change who gets the alarms** - Notification Class 1's start-up recipient is
`RECIPIENT_DEVICE_INSTANCE` (389108), by device instance; the stack finds the
address from its I-Am. `Recipient_List` is writable, so a workstation can
replace the list at run time (B-ALSC's "event distribution by another device",
L.5.1) - a real product should keep a written list across a restart.

**Change the latching and reset rules** - `FollowReading()`, `OperationFits()`,
`ApplyOperation()` and `OperationExpectedOf()` in `main.cpp` (the "logic internal
to the device" cl. 12.15 leaves a local matter; B-LSC-CPP's TUTORIAL explains
each). The stack checks only that a named object exists.

**Change the schedule** - Saffron's weekly entry, `Schedule_Default` and its
Calendar exception are set up in `main()` (B-AAC-CPP's canonical pattern). The
engine runs on the Device's `Local_Date` / `Local_Time`, which this file serves
from the device clock (`GetDeviceLocalTm`: host clock + the last
TimeSynchronization's offset). Serve both, or the schedule never runs (stack
#3958). Change the holidays in Calendar 1, not in the Schedule.

### Add a second analog input

Read this whole recipe before starting - the last step is the one that is easy
to miss and the one BTL will fail you for.

> **Why there are four edits, not three - and why skipping one is SILENT.**
> Most of the `GetProperty*` callbacks match on **both** object type *and*
> instance (`objectInstance == ANALOG_INPUT_INSTANCE`), so a new instance falls
> through every one of them. `GetPropertyBool` is the exception: it matches on
> type only (for `Out_Of_Service`), so that property works for a new instance
> for free.
>
> Here is the part that matters, and it is the opposite of what most people
> assume: falling through a callback does **not** reliably produce an
> error. The stack errors only for the few properties it refuses to invent -
> `Present_Value`, `Number_Of_States`, `Relinquish_Default`, `Local_Date`,
> `Local_Time`, and a Network Port's `APDU_Length`. For everything else it
> **silently substitutes a default**:
>
> | Property | If you forget to serve it | Loud? |
> |---|---|:--:|
> | `Present_Value` | Error (`read-access-denied`) | yes |
> | `Object_Name` | reads back as the string **`"undefined"`** | **no** |
> | `Units` | reads back as **`no-units` (95)** | **no** |
> | `Out_Of_Service` | served on type alone - works by accident | n/a |
>
> It is worse than "wrong value": the object's `Property_List` **still
> advertises `Units` (117)**. So the object actively claims to have the
> property, and then answers with a default. Nothing on the wire says you
> forgot anything.
>
> So a half-added object does not look broken; it looks **healthy**. Add two of
> them and both report `Object_Name "undefined"` - duplicate object names inside
> one device, which is a spec violation and a hard BTL failure that every scan
> tool will render as a perfectly good object. **"It scanned OK" is exactly the
> failure mode, not evidence against it.**

```cpp
// 1) a new instance number (in section 1).
//    Naming: a second object of a type is "<Colour> 2" - so Analog Input 2 is
//    "Bronze 2", NOT a new colour. Each object TYPE owns one colour series-wide.
static const uint32_t ANALOG_INPUT_2_INSTANCE = 2;   // "Bronze 2"
static float g_analogInput2Value = 23.1f;            // its live value

// 2) add the object (in main, next to the other BACnetStack_AddObject calls).
//    Check the return, like every other stack call in this file.
if (!BACnetStack_AddObject(g_deviceInstance, OBJECT_TYPE_ANALOG_INPUT, ANALOG_INPUT_2_INSTANCE)) {
    printf("Error: Failed to add Analog Input 2 (Bronze 2).\n");
    return 1;
}

// 3) serve its Present_Value + Object_Name:
//    GetPropertyReal:        AI/2 + Present_Value -> *value = g_analogInput2Value;
//    GetPropertyCharString:  AI/2 + Object_Name   -> "Bronze 2"

// 4) DO NOT SKIP: serve its Units, in GetPropertyEnumerated.
//    Units is a REQUIRED property of an Analog Input. The existing check reads
//    `objectInstance == ANALOG_INPUT_INSTANCE`, which is instance 1 - so without
//    this, reading Analog Input 2's Units returns an ERROR and the object is
//    NON-CONFORMANT. It will still appear in the Object_List and its
//    Present_Value will read back perfectly, so the device looks healthy right
//    up until BTL certification.
//    GetPropertyEnumerated:  AI/2 + Units -> *value = ENGINEERING_UNITS_DEGREES_CELSIUS;
```

Then re-run the README's Verify steps **against Analog Input 2**, not just Analog
Input 1 - read every required property and **diff it against Analog Input 1**.
Any property that comes back `"undefined"`, `no-units`, or `0` where object 1
returns something real is a step you missed. Because the failure is silent (see
the table above), this diff is the only thing that catches it.

## Life Safety Point/Zone at this Stack Pin (issue #2036)

At `6.x` @ `69b6249f` (as from `64b2cfac5`) the stack falls through to this file's callbacks for every
Life Safety Point/Zone property (stack #2187; up to `abd4cee1` it answered
`unknown-object` before reaching them). The stack's own life-safety engine is
still not exported (stack
[#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036), open), so:

- **Amber's and Azure's state is this file's** (`LifeSafetyObjectState`):
  `Tracking_Value` follows the detector, `Present_Value` latches alarm until a
  RESET, `Silenced` and `Operation_Expected` follow LifeSafetyOperation. Both are
  read-only on the wire, as Table 12-18 says.
- **`Reliability` comes from two places**: your callback serves cl. 13.2.2.2's
  first stage (hardware health - always `no-fault-detected` here) and the stack's
  `FAULT_LIFE_SAFETY` algorithm the second (`multi-state-fault` while
  `Present_Value` is fault); the stack serves the combination. Do not compute the
  algorithm's answer in the callback.
- **`Zone_Members` reads empty** - the only setter is test-tool only (TODO.md #1).

## What each object type needs you to serve

The application must serve every REQUIRED property the stack does not generate.
It differs per type - this is the checklist, so you do not have to infer it:

| Object type | You must serve | Plus |
|---|---|---|
| Analog Input | `Present_Value` (Real), `Object_Name`, `Units` | COV-subscribable |
| Binary Input | `Present_Value` (Enumerated), `Object_Name` | `Polarity` |
| Multi-State Input | `Present_Value` (Unsigned), `Object_Name` | `Number_Of_States`, `State_Text` |
| Analog/Binary/Multi-State Output | `Object_Name`, `Units`/`Polarity`/`Number_Of_States`, `Relinquish_Default` | commandable - `Present_Value`/`Priority_Array`/`Current_Command_Priority` resolved by the stack from the priority array you populate |
| Life Safety Point/Zone | `Object_Name`, `Present_Value`, `Tracking_Value`, `Reliability` (first stage only), `Out_Of_Service`, `Mode`, `Silenced`, `Operation_Expected` | from `LifeSafetyObjectState` (see the Life Safety section above) |
| Notification Class | `Object_Name` | `Priority`/`Ack_Required`/`Recipient_List` via `BACnetStack_AddNotificationClassObject`/`AddRecipientToNotificationClass`, not `GetProperty*`; `Recipient_List` made writable with `SetPropertyWritable` |
| Event Log | `Object_Name` | everything else held by the stack's own Event Log engine (`BACnetStack_AddEventLogObject`) |
| Schedule | `Object_Name`, `Reliability`, `Out_Of_Service` | `Present_Value`/`Effective_Period`/`Schedule_Default`/etc. held by the stack's Schedule engine |
| Calendar | `Object_Name` | stack-held (`BACnetStack_AddCalendarObject` + `AddCalendarDateEntry`): the stack keeps `Date_List` and derives `Present_Value` from `Local_Date` |

## Who serves what: the application or the stack?

The single most common question when reading this file is "who answers this
property?" For Analog Input 1 (a simple, fully-working object), the whole
picture:

| Property | Served by | How |
|---|---|---|
| `Object_Identifier` | **stack** | generated from the object you added |
| `Object_Type` | **stack** | generated |
| `Object_List` | **stack** | generated (Device object) |
| `Property_List` | **stack** | generated |
| `Status_Flags` | **stack** | generated |
| `Event_State` | **stack**, sort of | no intrinsic alarming on Bronze, so nothing serves it - it reads `normal` only because `normal` is the enumeration's zero value and the stack substitutes a datatype default. Correct by coincidence, not design. |
| `Out_Of_Service` | **you** | `GetPropertyBool` - matched on object **type only** |
| `Present_Value` | **you** | `GetPropertyReal` |
| `Object_Name` | **you** | `GetPropertyCharString` |
| `Units` | **you** | `GetPropertyEnumerated` |

Life Safety Point 1 "Amber" is served the same way, from its
`LifeSafetyObjectState` - except `Event_State` and `Reliability`, which the
stack computes from the two algorithms (see the Life Safety section above).

Every object, not just these two, is in [docs/PICS.md](docs/PICS.md).

## Reviewing your device

After you have changed anything, review it against the conformance statement
rather than against "it looked fine in the explorer":

1. Regenerate [docs/PICS.md](docs/PICS.md) after editing `docs/objects.json`
   (see [Keeping the PICS honest](#keeping-the-pics-honest) below). A ⚠ row is a
   required property nothing serves.
2. Read **every** property listed for **every** object with a BACnet client, and
   compare the value against the PICS. `"undefined"`, `no-units` and `0` are the
   three shapes a missed callback takes. `tests/run_wire_tests.py` reads every
   listed property and fails on any that does not return a value.
3. Diff a new object of a type against the existing one of that type. Anything
   that differs and shouldn't is a callback that matched on instance.
4. Confirm a write to a read-only input (e.g. Emerald, or Bronze while it is in service) is rejected, and that a
   write to a commandable output (e.g. Chartreuse) at a priority is accepted,
   read back, and relinquishes correctly to `Relinquish_Default` on NULL.
5. Run the Wire Tests (`tests/run_wire_tests.py`): they play the life-safety
   scenario, the detector fault, the Event Log, the recipient-list rewrite and
   the schedule, and the Failure Modes. If you changed a rule, change its test,
   and check the test fails without your change (mutation-verify it -
   `tests/README.md`).

### Keeping the PICS honest

`docs/PICS.md` is partly generated. `docs/objects.json` describes each object and
who serves which property; the series tool regenerates the object tables from it
plus the CAS BACnet Stack's property profiles (a reference the series tool vendors):

```bash
python tools/gen-objects-properties.py BACnetProfileExample-B-ALSC-CPP            # rewrite
python tools/gen-objects-properties.py BACnetProfileExample-B-ALSC-CPP --check    # fail if stale
```

(That tool lives in the example-series repository, not in this one. If you only
have this repository, edit the generated block by hand and keep it matching the
callbacks in `main.cpp`.)

When you add an object or a property to `main.cpp`, update `docs/objects.json`
in the same change and regenerate. The `app` list is what the callbacks serve;
`accepted` is for a required property you deliberately leave to the stack's
default (or, for Amber/Azure, that the stack cannot currently reach at all),
and each one needs a justification. Anything required, not in `app` and not in
`accepted`, comes out as a ⚠ row - that is a defect, not a feature.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| On start-up the app prints a wall of red `Error:` lines but the device works | **Expected - this is not your bug.** Two benign sources, both from the stack's own debug logging: (1) the device receives its **own** broadcast I-Am and logs a decode cascade (*"Services is not supported service=[0]"* ... *"Failed to process the incoming NPDU"*) - any BACnet/IP device that listens for broadcasts hears itself; (2) a one-time *"UUID has not been set. A UUID must be set for the BACnetSC device to start."* - the stack starts a BACnet/SC datalink these IP-only examples never configure. On a healthy start-up roughly half the output is these lines. |
| The example stops at start-up with `Error: Failed to enable the LifeSafetyOperation (AE-LS-B) ...` | The stack was built without `STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION`. A SOURCE build gets it from `CMakeLists.txt`; a STATIC/DLL library must be rebuilt with it - README "Build". |
| No alarm reaches the workstation | It has not announced itself: Crimson names it by device instance (389108). Read the Device's `Device_Address_Binding`; make the workstation send an I-Am - or write it into `Recipient_List` by address. |
| Event Log 1's `Record_Count` stays 0 | `Enable` starts FALSE (stack #3301): write it TRUE. |
| A RESET gets `Error(object, invalid-operation-in-this-state)` | By design: the detector still sees smoke, or nothing is latched. |
| `ReadProperty`/`WriteProperty` to Amber or Azure answers `unknown-object` | You are on a stack older than `6.x` @ `64b2cfac5` (fixed by stack #2187). Move the Stack Pin forward; see [Life Safety Point/Zone at this Stack Pin](#life-safety-pointzone-at-this-stack-pin-issue-2036) above. |
| CMake error: *"CAS BACnet Stack adapter not found under: ..."* | Submodules not initialized. Run `git submodule update --init --recursive` (or pass `-D CAS_STACK_DIR=...`). |
| `CASBACnetStackDLL.h: No such file or directory` | Same - submodules not checked out. |
| Windows: *"No CMAKE_CXX_COMPILER could be found"* | Install Visual Studio with the "Desktop development with C++" workload, then re-run from a fresh terminal. |
| First build seems stuck for minutes | Normal - it's compiling ~600 stack files. Only the first build is slow. |
| App prints *"Failed to bind UDP port 47808"* | Another BACnet program is already using 47808. Stop it, or run with `--port <n>`. |
| Client sends Who-Is but sees no I-Am | Firewall is blocking UDP 47808, or the client and device are on different subnets (Who-Is is a broadcast). Allow the port; test on the same subnet first. |
| Replies show an unexpected device instance or vendor | Another BACnet device is already answering on this host/port. On Linux/macOS two processes can share the port and both reply; on Windows the example asks for `SO_EXCLUSIVEADDRUSE` (`common/SimpleUDP.cpp`) so this shows up as a bind failure instead. Stop the other device, or use `--port`. |
