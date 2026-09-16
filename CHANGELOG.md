# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
  running this repository's own built binary against a live `bacpypes3`
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
