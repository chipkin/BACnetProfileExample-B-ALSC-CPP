# AGENTS.md

Guidance for AI coding agents working in this repository. See
<https://agents.md/> for the format. Human contributors should read
[README.md](README.md) first, then [TUTORIAL.md](TUTORIAL.md).

## What this project is

A **tutorial** C++ example of the BACnet **B-ALSC (Advanced Life Safety
Controller)** profile, and it is **Profile-functional** (the series bar). It is
B-LSC-CPP's example (a SIMULATED smoke detector drives Life Safety Point 1
"Amber" and its zone "Azure" to a latched life-safety alarm; confirmed
notifications go to an operator workstation; LifeSafetyOperation /
AcknowledgeAlarm silence, acknowledge and reset it) plus B-ALSC's additions:
Notification Class 1's `Recipient_List` is writable (event distribution by
another device), Event Log 1 "Beige" logs every alarm (ReadRange), and Schedule 1
"Saffron" + stack-held Calendar 1 "Cream" (B-AAC's canonical pattern) run on a
device clock TimeSynchronization sets. Wire Tests against Python Peers prove each,
with the Failure Modes. What the customer interface still cannot do (Zone's
`Zone_Members`, stack #2036; Event Log enabled at start-up, stack #3301) is a
`[KNOWN GAP]` in [TODO.md](TODO.md) and the Wire Tests - keep both honest and
current. The top priority is that the code reads like a tutorial a customer can
learn from and copy-paste. Favour clarity over cleverness.

## Layout

This repository is self-contained:

- `main.cpp` - the example device: B-LSC-CPP's main.cpp plus the B-ALSC
  additions (keep the two diffable). Section 1b is the smoke-detector SIMULATION.
- `simulation/` - the Wire Tests' loopback-only test control channel (SIMULATION,
  off unless `BALSC_SIMULATION_CONTROL_PORT` is set). Never a CLI option.
- `common/` - the shared helper (vendored).
- `README.md` - what this example is. Keep it short and about THIS example only.
- `TUTORIAL.md` - how to extend and review the example, including the Life
  Safety Point/Zone history (issue #2036) in detail. Long-form material that would
  bloat the README belongs here.
- `docs/PICS.md` - the Protocol Implementation Conformance Statement. Its
  objects-and-properties section is GENERATED from `docs/objects.json`; do not
  hand-edit between the `OBJECTS-PROPERTIES` markers.
- `docs/objects.json` - the input to that generator. Update it in the same change
  as any `main.cpp` change that adds an object or a `GetProperty*`/`SetProperty*`
  branch.
- `TODO.md` - what B-ALSC requires but the stack's customer surface cannot yet
  do, and why. Keep it honest and current.
- `tests/` + `wiretest/` - the Wire Tests (discovery, `configuration_test.py`,
  life safety, fault, Event Log, distribution, schedule) and the series' shared harness
  (vendored at 0.7.0; change it only as the series does, in every example).
  Every check must fail when its feature is removed: mutation-verify any change.
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack** as a git submodule
  (private; compiled from source). After cloning, run
  `git submodule update --init --recursive`.

The `PROFILE-TABLE` block in README.md is also generated, from the example-series
repository's `docs/profile-table.md`. Edit it there, not here.

## Build

Plain CMake, identical on every platform, in the adapter's default SOURCE mode
(the stack's sources are compiled into the executable - no prebuilt library, no
DLL, no per-platform pre-step):

```bash
git submodule update --init --recursive   # once, if not cloned with --recursive
cmake -B build -S .
cmake --build build --config Release
```

The first build compiles the whole stack (~600 files) and takes a few minutes;
rebuilds after that are incremental and fast. Use `-D CAS_STACK_DIR=...` only if
your stack lives outside the bundled submodule. Do not reintroduce a link-mode
flag or a series-root build script into the documented build: a customer
downloads this repository on its own and must be able to build it with the two
commands above.

## Run

```bash
./build/BACnetExampleBALSC [--port 47808] [--deviceID 389008] [--deviceName "Chipkin Example B-ALSC"]   # Linux/macOS
.\build\Release\BACnetExampleBALSC.exe [--port 47808] [--deviceID 389008] [--deviceName "Chipkin Example B-ALSC"]   # Windows
```

Interactive keys while running: `h` help, `q` quit, up/down nudge Analog Input 1
(also feeds its COV subscribers), `s` add a Weekly_Schedule transition to Schedule 1
("Saffron") for right now (device clock). The detector has no key: the Wire Tests
use the test control channel (README "Interactive commands").

## Conventions

- Device is named "Chipkin Example B-ALSC"; objects use the series' colour names; vendor id 389.
- Implement the B-ALSC services the stack supports; expose **every required
  property** of each object for Protocol_Revision 30. Anything B-ALSC requires that
  is NOT implemented must be listed in [TODO.md](TODO.md) and the README.
- **Life Safety Point/Zone objects use the SAME generic pattern as every other
  object in this series** - `BACnetStack_AddObject` + this file's own Get/Set
  callbacks holding the state - NOT the stack's internal
  `BACnetStackLifeSafetyPoint`/`Zone` engine, whose configuration surface
  (`AddLifeSafetyPointObject`, `SetLifeSafetyZoneMembers`,
  `SetLifeSafetyAcceptedModes`/`AlarmValues`/`FaultValues`, and
  `SetLifeSafetyTrackingValue`) is internal to `BACnetDBDevice` and is not
  exported through `CASBACnetStackDLL.h`. Re-verify this with a fresh
  `grep -n "DllExport.*LifeSafety" source/CASBACnetStackDLL.h` before assuming it
  has changed - it is the load-bearing fact behind this file's whole life-safety
  design (see the file header comment in `main.cpp`).
- Intrinsic life-safety alarming: arm an object with
  `SetIntrinsicChangeOfLifeSafetyAlgorithm` / `SetFaultLifeSafetyAlgorithm` + a
  Notification Class (`AddNotificationClassObject` +
  `AddRecipientToNotificationClass`) + `SetAlarmsAndEventsForObjectEnabled(...,
  true)`. Drive the monitored `Present_Value` and call `BACnetStack_UpdateValue`
  so the stack re-evaluates and fires the notification - the doc comment on that
  function is not decorative: "a host that never calls it will never generate an
  event notification."
- LifeSafetyOperation: needs `STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION` (the
  stack's documented public toggle, defined in `CMakeLists.txt` for SOURCE builds;
  a STATIC/DLL library must be built with it), plus
  `BACnetStack_RegisterCallbackLifeSafetyOperation` and the service enabled. The
  stack checks the named object exists; the callback decides whether the operation
  fits the object's current state (`OperationFits()`), refusing with
  `INVALID_OPERATION_IN_THIS_STATE`. `useObjectIdentifier == false` means "all
  applicable objects" (cl. 13.13.1.1.4).
- Reliability on Amber/Azure: the callback serves only cl. 13.2.2.2's first stage
  (no-fault-detected); the stack's FAULT_LIFE_SAFETY algorithm supplies
  `multi-state-fault` and serves the combination. Do not compute it in the callback.
- The device clock: `Local_Date` / `Local_Time` come from `GetDeviceLocalTm` (host
  clock + the last TimeSynchronization's offset); the Schedule and Calendar
  engines run on them, and must have them served (stack #3958).
- DS-COV-B: `BACnetStack_SetPropertySubscribable` on the property, plus
  `SetCOVSettings`/`SetMaxActiveCOVSubscriptions`; `BACnetStack_UpdateValue` also
  feeds COV subscribers - one call does both jobs, there is no separate "notify
  COV" export.
- Outputs are **commandable**: store the 16-slot `Priority_Array` +
  `Relinquish_Default` in the app (the `Commandable` struct); let the stack
  resolve `Present_Value`. Writes land via the `SetProperty*` callbacks (value)
  and `SetPropertyNull` (relinquish).
- DeviceCommunicationControl (DM-DCC-B): the stack runs the enable/disable state
  machine; the `DeviceCommunicationControl` callback just validates `DCC_PASSWORD`
  and logs. The deprecated plain `disable` (1) is rejected by the stack at
  Protocol_Revision >= 20 - only `enable` (0) and `disable-initiation` (2) apply.
- ReinitializeDevice (F-REINIT, canonical here): never restart inside the
  callback - record a deadline (`CASExampleHelper::RequestRestart`), return true
  so the `SimpleACK` ships on the next `BACnetStack_Tick()`, and perform the
  actual restart from the main loop once `RestartDue()` says the deadline passed.
- Match the surrounding code style: `const`-correct parameters, check every stack
  return value, keep `main.cpp` linear and well-commented.
- **Never edit `common/` in this repo alone** - it is a vendored copy shared by
  every example in the series, with its own version (`COMMON_VERSION`) and
  changelog (`common/CHANGELOG.md`). To change it: edit, bump the version, add
  a changelog entry, then re-copy `common/` into every example repository.

## How to verify a change

The Wire Tests are the verification (README "Wire Tests", `tests/README.md`):

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBALSC
```

They cover discovery (every listed property reads), the life-safety scenario and
its Failure Modes, the detector fault, the Event Log (ReadRange), the
`Recipient_List` rewrite, and the schedule under TimeSynchronization. Not covered
(do these by hand when you touch them): COV notifications, a silent recipient's
retransmissions, UNSILENCE, DCC, ReinitializeDevice and the `s` key.

When you change behaviour, change its test and **mutation-verify** it: remove or
break the feature, rebuild (check the binary's mtime changed), confirm the check
fails, restore. If you changed the objects or their properties, regenerate
`docs/PICS.md` (`python tools/gen-objects-properties.py BACnetProfileExample-B-ALSC-CPP`
from the series root) and confirm no row comes out flagged with ⚠.

## Releasing

Bump `APP_VERSION` in `main.cpp` and add an entry to [CHANGELOG.md](CHANGELOG.md),
then tag `vX.Y.Z`. The GitHub Actions workflow builds and publishes the release.

## License

See [LICENSE](LICENSE). The CAS BACnet Stack is a separate, commercially
licensed product and is not covered by it.
