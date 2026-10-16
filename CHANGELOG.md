# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - unreleased

Profile-functional rework (series bar, `docs/GLOSSARY.md`; brief
`docs/phase2-rework-brief.md` in the example-series folder), on top of
BACnetProfileExample-B-LSC-CPP 1.2.0's. Stack Pin unchanged (`6.x` @ `64b2cfac5`),
`common/` 3.4.0 and `wiretest/` 0.6.0 unchanged.

Profile Function, 135-2024 L.5.1 (verbatim): "A B-ALSC device performs life safety alarm
detection and control. It supports life safety objects and limited modification of its
alarm and event reporting, including event distribution by another device. Also, the
device supports scheduling of internal values and event logging."

### Added

- **Everything B-LSC-CPP 1.2.0 added**, merged into this file (a 3-way merge of B-LSC's
  change, so the two `main.cpp` files still diff to the B-ALSC additions): the simulated
  smoke detector and loopback test control channel (`BALSC_SIMULATION_CONTROL_PORT`),
  latching `Present_Value`, LifeSafetyOperation compiled in and executed with the
  state rules (reset refused while smoke is present / nothing latched / RESET_FAULT),
  confirmed notifications to Device 389108 by device instance, `Number_Of_APDU_Retries`
  3, Reliability served as cl. 13.2.2.2's first stage only, the AcknowledgeAlarm
  callback leaving 13.5.2 to the stack.
- **Notification distribution by another device** (L.5.1): Crimson's `Recipient_List` is
  writable; `tests/distribution_test.py` redirects it.
- **Wire Tests**: `life_safety_test.py` (37 + 1 known gap) and `fault_test.py` (13), as
  B-LSC's; `event_log_test.py` (17 + 1 known gap), `distribution_test.py` (7),
  `schedule_test.py` (5, B-AAC-CPP's); `alsc_setup.py`; `wiretest_extras.py` (B-LSC's
  generic helpers plus B-AEC-CPP's ReadRange / Event Log record decoders, verbatim).

### Changed

- **Calendar 1 "Cream" is stack-held** (`BACnetStack_AddCalendarObject`, Date_List =
  December 25 every year) and Saffron's exception references it, replacing the empty
  plain-`AddObject` Calendar and the inline 2026-12-25 exception (B-AAC-CPP's canonical
  pattern).
- **The device clock**: `Local_Date` / `Local_Time` are the host clock plus the last
  TimeSynchronization's offset (`GetDeviceLocalTm`, B-AAC-CPP's), so a time sync moves
  Saffron and Cream; before, a sync only overwrote a snapshot. The `s` key uses the
  device clock too.
- **Event Log 1 "Beige"** is now proved to log each alarm exactly once, even with the
  recipient unreachable (the 1.1.0 check saw 2 records per transition: the broadcast
  recipient, stack #3957). `Enable` still starts FALSE (stack #3301, `[KNOWN GAP]`).
- `Present_Value` of Amber and Azure read-only again (Table 12-18).
- README (scenario, Failure Modes, what is Simulation, Build note, Wire Tests), TUTORIAL,
  PICS (regenerated; Number_Of_APDU_Retries, Reliability, Recipient_List, Calendar rows),
  AGENTS, TODO (rewritten), tests/README, release.yml step name. APP_VERSION 1.1.0 ->
  1.2.0.
- Wire Tests use the shared `wiretest/` 0.7.0: `tests/wiretest_extras.py` is folded into it (`wiretest.services` life safety and ReadRange / Event Log records, `wiretest.SimulationControl`, `Workstation.announce`), and `request_with_retry` is `wiretest.Workstation(retries=1)`.

### Verified (2026-10-16)

- Windows 11 STATIC (NMake, VS 18; stack `ReleaseLib|x64` rebuilt with
  `CL=-DSTACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION`): 0 warnings; Wire Tests 100/100 x3
  (21 + 37 + 13 + 17 + 7 + 5), 2 known gaps. Runs 2 and 3 each show one visible `[RETRY]`
  (a request with no answer, sent again - the host was busy with other sessions' builds).
- Linux WSL Ubuntu 22.04 SOURCE: Wire Tests 100/100 x3, 2 known gaps, no `[RETRY]`.
- 19 mutations of `main.cpp` (Linux; B-LSC's 13 plus 6 for the B-ALSC additions), each
  rebuilt (relink checked) and run; every one fails at least one check - see the commit message.

## [1.1.0] - unreleased

### Changed

- **`common/` 3.3.0 -> 3.4.0**, copied verbatim from B-SS-CPP `5d78299`: `HelperSendMessage`
  sends a broadcast addressed to this socket's own address to the subnet broadcast instead of
  unicast to itself (stack #3933). README version lines updated.
- **`wiretest/` 0.5.0 -> 0.6.0**, copied verbatim from B-LS-CPP. Backward compatible: it adds
  codec helpers, `wiretest.SimulatedServer`, `wiretest.alarm`, `wiretest.Workstation` and
  `wiretest.wait_until`; the existing tests are unchanged.
- `tests/discovery_test.py` sends its Who-Is once more, with a visible `[RETRY]` line, when no
  I-Am comes back in 3 s (`tools/patch-discovery-whois-retry.py` from the example series).
  Who-Is is unconfirmed, so nothing else retries it, and the example's UDP receive can drop a
  datagram on Windows (`common/` SimpleUDP).
- **Stack Pin moves to `6.x` @ `64b2cfac5` (6.0.23)** from `6.x` @ `abd4cee1`
  (6.0.21), per the series rule that a pin moves to the latest `6.x` whenever an
  example is updated. Based on `origin/main` (`515a192`); no local work was
  unpushed and every other branch is older than main.
- **Life Safety Point 1 "Amber" and Life Safety Zone 1 "Azure" work over the
  wire at this pin.** Up to `abd4cee1` both answered `unknown-object` for almost
  every property (the old TODO.md item 0). Stack #2187 makes the stack fall
  through to this example's callbacks: every listed property reads, and a
  WriteProperty of `Present_Value` drives the intrinsic algorithms. The README,
  TUTORIAL, AGENTS.md, PICS and `main.cpp` header no longer call this example
  blocked; stack #2036 stays open for `Zone_Members` (TODO.md item 1).
- **Protocol_Revision 24 -> 30** (the stack's default at the new pin).
- **Segmentation is now supported** (`segmented-both`), by the stack (stack
  #2992). `docs/PICS.md` section 5 updated and the objects block regenerated.
- **`common/` 3.0.0 -> 3.3.0**, copied verbatim from B-SS-CPP `b640a81`.
- README, TUTORIAL, AGENTS.md and PICS version lines: stack 6.0.23, `common/`
  3.3.0, Protocol_Revision 30. README profile table re-synced. APP_VERSION
  1.0.2 -> 1.1.0.

### Fixed

- **An alarm(2) now raises LIFE_SAFETY_ALARM, as the docs always said.**
  `BACnetStack_SetIntrinsicChangeOfLifeSafetyAlgorithm` was given alarm(2) as an
  `alarmValues` entry, which the stack documents as driving the object to
  OFFNORMAL; it is now a `lifeSafetyAlarmValues` entry. Checked over the wire:
  Amber `Present_Value` 2 -> `Event_State` life-safety-alarm (it read offnormal
  before), 3 -> fault, 0 -> normal, one event notification each.
- **Local_Date and Local_Time read as values.** Executing TimeSynchronization
  makes the stack list both on the Device (135-2024 Table 12-13 footnotes 3 and
  4), but nothing served them, so both reads failed `value-not-initialized`. The
  discovery Wire Test found it. The example now serves them from the host clock,
  updated by TimeSynchronization, the way B-LD-CPP does. That also fixed
  **Schedule 1's Present_Value**, which read `value-not-initialized` too: the
  stack's Schedule engine works from Local_Date. It now reads 20.0
  (`Schedule_Default`).
- **Event Log 1 capturing Amber's alarms is no longer described as blocked.**
  At this pin, with `Enable` written TRUE (it starts FALSE), Amber
  `Present_Value` 2 / 0 / 3 / 0 moved `Record_Count` 1 -> 3 -> 5 -> 7 -> 9. The
  README no longer says a ReadProperty of `Log_Buffer` answers an empty list:
  the stack refuses it with PROPERTY / READ_ACCESS_DENIED, as cl. 12.27.13
  requires. Calendar 1's notes no longer cite #963 (closed) as the reason its
  Date_List is empty.
- **AE-LS-B is marked as met in part, not ✅.** AE-LS-B includes executing
  LifeSafetyOperation (135-2024 K.2.13), which the default stack build does not
  compile, so this example cannot silence or reset. TODO.md item 2 no longer
  says DM-LSO-B is "not a BIBB this profile requires" or that enabling it needs
  a stack edit (the example's own CMake can define the option; phase-2 work).
- AE-ACK-B and AE-INFO-B are marked "configured; not verified" until a test
  exercises them.

### Added

- **Wire Tests** (`tests/`, README "Wire Tests"): `tests/discovery_test.py`, the
  series' discovery test from B-SS-CPP `da3e96f` with this example's
  fourteen objects as its control, plus one spec-required refusal: Event Log 1's
  `Log_Buffer` must answer PROPERTY / READ_ACCESS_DENIED (cl. 12.27.13,
  15.5.1.3.1). CI runs it on Linux after the smoke test. Result: 21/21, 214 reads on Windows (STATIC) and Linux (SOURCE).
- `wiretest/` 0.5.0, the series' shared Wiretest Harness, vendored verbatim from
  B-BBMD-CPP `75aedd8`.

## [1.0.2] - unreleased

### Changed

- **Device renamed from the series' colour placeholder "Rainbow" to "Chipkin
  Example B-ALSC"** so devices from different examples in the series are
  distinguishable from each other on the same BACnet network - every example
  previously announced the identical Object_Name "Rainbow", which made two
  examples on one subnet indistinguishable by name. Sub-object names (Analog
  Input 1 "Bronze", etc.) are unchanged - only the Device object's name
  changed. `docs/colour-table.md` (series root) updated to match. APP_VERSION
  bumped 1.0.1 -> 1.0.2.

## [Unreleased]

## [1.0.1] - 2026-09-22

### Fixed

- **`Application_Software_Version` (12) and `Firmware_Revision` (44) were
  hardcoded and stale** - `main.cpp` set both from separate `static const
  char* FIRMWARE_REVISION = "1.0.0"` / `APPLICATION_SOFTWARE_VERSION =
  "1.0.0"` constants that nobody updated as the example's real version
  advanced past `1.0.0`, and `Firmware_Revision` was never meant to be this
  example's own version at all - it names the underlying platform. Fixed to
  match the pattern already proven in `BACnetProfileExample-B-SCHUB-CPP`
  (v1.1.13): `Application_Software_Version` now reads `APP_VERSION` directly
  (one source of truth, can't drift from `--version`'s own banner again).
  `Firmware_Revision` is now built at runtime from the CAS BACnet Stack's own
  `BACnetStack_GetAPIMajorVersion()`/`GetAPIMinorVersion()`/
  `GetAPIPatchVersion()`/`GetAPIBuildVersion()` (the same 4 calls
  `common/CASExampleHelper.cpp`'s `PrintVersion()` already uses for the
  startup banner), populated once into `g_firmwareRevision` right after
  `LoadBACnetFunctions()` succeeds. Verified with a real ReadProperty
  (bacpypes3) against the running device: `Application_Software_Version =
  "1.0.1"`, `Firmware_Revision = "6.0.21.0"` - both now match the actual
  running build instead of a stale hardcoded `"1.0.0"` string.

### Changed

- Restructured documentation to match the series' `README.md` +
  `TUTORIAL.md` + `docs/PICS.md` shape (matching
  `BACnetProfileExample-B-SS-CPP`): `README.md` is cut down to this example
  only (series framing, the generic profile explainer, "Before you ship", and
  the generated objects-and-properties block moved or removed); the
  extending/reviewing/Troubleshooting material moves to the new
  `TUTORIAL.md`; a new `docs/PICS.md` (ANSI/ASHRAE 135 Annex A shape) holds
  the conformance statement, including a Device object entry in
  `docs/objects.json` that was previously missing from the generated tables.
  The Life Safety Point/Zone `unknown-object` gap
  ([cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036))
  is carried forward precisely into all three documents and into
  `docs/PICS.md` section 6 as a configured-but-non-functional row.
- **Build switched from a prebuilt STATIC library to the adapter's default
  SOURCE mode**: `cmake -B build -S .` / `cmake --build build --config
  Release` is now the full, single-command-pair build on every platform, with
  no `tools/build-stack-static.sh` step. `CMakeLists.txt`'s header comment,
  `AGENTS.md`, and `.github/workflows/release.yml` (dropped the static-library
  cache/build steps and the matrix `lib:` entries; link-mode assertion now
  checks `SOURCE`; `metrics-*.json` records `"link_mode": "SOURCE"`; packaged
  release artifacts now include `TUTORIAL.md` and `docs/PICS.md`) were updated
  to match. The published v1.0.0 footprint numbers were measured under the old
  STATIC build; the README's Footprint table now notes that the next release
  refreshes them under the SOURCE build.
- Absorbed the README's former "Before you ship" table into per-field
  comments next to the `CHANGE ALL OF THIS BEFORE YOU SHIP` block in
  `main.cpp`, including the `DEVICE_NAME` uniqueness warning.

## [1.0.0] - 2026-09-15

### Added

- Initial **B-ALSC (Advanced Life Safety Controller)** profile example for the
  CAS BACnet Stack in C++. Seeded from B-LSC (Life Safety Controller)'s
  `implement-lsc` branch content (PR open, not yet merged there at the time
  this was written); implements every B-ALSC capability the standard stack's
  customer-facing API exposes; documents the inherited gap plus one new
  consequence in [TODO.md](TODO.md).
- Carries B-LSC's full object model unchanged: Device "Rainbow" (389008,
  changed from B-LSC's 389007), read-only inputs (Analog "Bronze" / Binary
  "Emerald" / Multi-State "Hot Pink"), commandable outputs (Analog
  "Chartreuse" / Binary "Fuchsia" / Multi-State "Indigo"), Life Safety Point 1
  "Amber" / Life Safety Zone 1 "Azure" with intrinsic ChangeOfLifeSafety +
  fault algorithms, Notification Class 1 "Crimson", LifeSafetyOperation
  responder (implemented, not enabled - see below), AE-ACK-B, AE-INFO-B,
  DS-COV-B on Bronze/Amber, F-REINIT, DS-RPM-B/DS-WPM-B, DM-DCC-B, DM-TS-B/
  DM-UTC-B, DM-DDB-A/B, DM-DOB-B, and Network Port "Vermilion".
- **F-EVENTLOG (canonical for this series):** Event Log 1 "Beige" (type 25,
  `BACnetStack_AddEventLogObject`). Its core properties (`Enable`,
  `Buffer_Size`, `Record_Count`, `Total_Record_Count`, `Log_Buffer`, ...) are
  held and served by the stack's own Event Log engine; `Log_Buffer` is read
  with **ReadRange** (service 35). Verified over the wire: `Object_Name`/
  `Object_Type`/`Buffer_Size`/`Record_Count`/`Total_Record_Count` read
  correctly, `Enable` round-trips a WriteProperty, `ReadRange` succeeds and
  the automatic capture hook was independently confirmed live (toggling
  `Enable` was captured as a clause-12.27 log-status record with no
  application code involved). Capturing Amber's/Azure's own alarm is blocked
  by the same stack gap as the Life Safety objects - see TODO.md #3.
- **F-SCHED-I:** Schedule 1 "Saffron" + Calendar 1 "Cream" (type 17/6),
  copied byte-for-byte from B-AAC's canonical pattern. Saffron writes Analog
  Output 1 "Chartreuse" `Present_Value` at priority 8 on a weekly + one-off
  exception basis (`Schedule_Default` 20.0 otherwise); the `s` key (claimed by
  B-AAC, `common/` 2.1.0+) adds a transition for right now. Calendar 1
  "Cream"'s `Date_List` cannot be populated through the customer API (issue
  #963, same gap B-AAC found) - `Present_Value` always answers `false`.
  Verified over the wire: `Object_Name`, `Priority_For_Writing` and
  `Schedule_Default` read back correctly on Saffron; `Object_Name` and
  `Present_Value` on Cream.
- Linked against the CAS BACnet Stack `6.x` @ `abd4cee1` (reports 6.0.21) as a
  prebuilt **STATIC** library (`CAS_BACNET_STACK_LINK=STATIC`), built by
  `tools/build-stack-static.sh` from the stack's own project files.
- `common/` vendored at **v2.5.0**, byte-identical to the rest of the series
  (copied verbatim from B-SS-CPP for this task).
- All required Protocol_Revision 24 properties across every object except
  the documented Life Safety Point/Zone gap; strict build warnings on the
  example's own sources; zero warnings from `main.cpp`/`common/`.

### Not yet implemented (see [TODO.md](TODO.md))

- **⚠ CRITICAL: Life Safety Point 1 (Amber) and Life Safety Zone 1 (Azure)
  cannot serve almost any property.** Inherited from B-LSC, re-verified by
  running this repository's own built binary against a live BACnet
  client: `Object_List`/`Object_Type` are correct, but `Object_Name`,
  `Present_Value`, `Out_Of_Service`, and the WriteProperty this repo's own
  alarm/fault demo relies on all answer `unknown-object`. Root cause is in
  the stack, not this example's code. See TODO.md #0 and
  [chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036).
- **Life Safety Zone 1 (Azure)'s `Zone_Members`** - no customer-facing callback
  can serve this required, constructed property (inherited from B-LSC). See
  TODO.md #1.
- **LifeSafetyOperation (service 37) not enabled** - inherited from B-LSC; the
  linked static library was compiled without
  `STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION`. See TODO.md #2.
- **⚠ Event Log 1 (Beige) cannot demonstrate capturing Amber's/Azure's own
  alarm** - new to this repository, but downstream of the SAME root cause as
  the Life Safety gap above, not a new stack defect. See TODO.md #3.

[1.0.0]: https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP/releases/tag/v1.0.0
