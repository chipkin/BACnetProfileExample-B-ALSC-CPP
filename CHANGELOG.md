# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No changes yet._

## [1.3.0] - 2026-10-27

Built on CAS BACnet Stack 6.x (69b6249f).

### Added

- **Analog Input 1 (`Bronze`) can be taken out of service** (cl. 12.2.10).
  `Out_Of_Service` is writable, and while it is TRUE `Present_Value` is decoupled
  from the sensor and writable (cl. 12.2.4), so a client can simulate a reading and
  drive COV notifications and the OUT_OF_SERVICE bit of `Status_Flags`. In
  service, a write of `Present_Value` is refused (WRITE_ACCESS_DENIED), as before.
  A coldstart puts the object back in service.
- **`--deviceName <text>`**: sets the Device's Object_Name at start-up, like
  `--deviceID` sets its instance. Object_Name must be unique on a BACnet
  internetwork, so two units no longer have to share the built-in name. The
  default is unchanged (`Chipkin Example B-ALSC`). A name must be 1 to 255 bytes
  with no control characters, otherwise the example warns and keeps the default.
  The name cannot be changed over the network.
- **Automated self-test** `tests/configuration_test.py` checks `--deviceID` and
  `--deviceName`.

### Changed

- **`--help` lists only the options the example reads.** It no longer lists
  `--dcc-password` (the password is `DCC_PASSWORD` in `main.cpp`). `--xml`, which
  was listed but did nothing, now prints each received and sent frame as XML.
- **SubscribeCOV accepts lifetimes up to 8 hours** (28800 s, was 1 hour), as
  DS-COV-B requires.
- **ReinitializeDevice START_BACKUP and START_RESTORE** (backup and restore are
  not supported) are answered with an Error (OPTIONAL_FUNCTIONALITY_NOT_SUPPORTED)
  instead of an Abort.
- **Self-tests** default to UDP port 47836 (was 47821).
- **Documentation**: PICS lists Database_Revision as 14 (one per object added at
  start-up), marks I-Am as executed as well as initiated (DM-DDB-A), lists Who-Is
  and the COV notifications as initiated, and lists Life Safety Point
  `Property_List` and the Event Log's `Stop_When_Full`, `Buffer_Size`,
  `Log_Buffer`, `Record_Count` and `Total_Record_Count`. The PICS objects tables
  cite the stack's property profiles.
- Vendored `common/` updated to 3.5.0 (see `common/CHANGELOG.md`).

### Fixed

- **Analog Input 1 now has `COV_Increment`** (reads 1.0), which cl. 12.2 requires
  on an Analog Input that supports COV reporting.
- **The Device's `Description` read as an empty string.** It was longer than the
  stack's 255-octet limit and was refused. It is now 227 characters, and the
  helper truncates to the limit.
- **Requests no longer go unanswered on Windows.** A request that arrived just as
  the socket's short receive timeout expired could be silently dropped. The
  receive loop now waits with `select()` (vendored `common/` 3.4.1).

## [1.2.0] - 2026-10-16

The example now works as a B-ALSC (Advanced Life Safety Controller): a simulated
smoke detector drives the life safety objects, alarms are reported and logged, and
notification distribution can be redirected. Built on CAS BACnet Stack 6.x
(64b2cfac5, reports 6.0.23).

### Added

- **Simulated smoke detector** drives Life Safety Point 1 "Amber".
  `Tracking_Value` follows it; `Present_Value` latches `alarm` until a
  LifeSafetyOperation RESET; a detector fault shows as a fault state. Life Safety
  Zone 1 "Azure" rolls Amber up. The automated self-tests move the detector
  through a loopback-only control channel that is off unless
  `BALSC_SIMULATION_CONTROL_PORT` is set.
- **LifeSafetyOperation is executed** (AE-LS-B). SILENCE and UNSILENCE set
  `Silenced`; RESET and RESET_ALARM unlatch. A reset while the detector still
  sees smoke, a reset of an object that is not latched, and every RESET_FAULT are
  refused with OBJECT / INVALID_OPERATION_IN_THIS_STATE (cl. 13.13).
- **Alarms go to a recipient**: Notification Class 1 names the operator workstation
  by device instance (389108), confirmed. `Number_Of_APDU_Retries` is 3, so a
  confirmed notification is retransmitted.
- **Notification distribution by another device**: Notification Class 1's
  `Recipient_List` is writable.
- **Event Log 1 "Beige"** records each alarm exactly once and is read with
  ReadRange. Its `Enable` still starts FALSE and must be written TRUE.
- **Schedule 1 "Saffron" and Calendar 1 "Cream"**: Cream is held by the stack
  (Date_List is December 25 every year) and Saffron's exception references it.
  `Local_Date` and `Local_Time` follow the host clock plus the last
  TimeSynchronization, so a time sync moves Saffron and Cream.
- **Automated self-tests** under `tests/` (Python standard library only) for
  discovery, the life safety scenario, fault handling, the event log,
  distribution and the schedule.

### Changed

- **`Present_Value` of Amber and Azure is read-only** (Table 12-18): only the
  detector and LifeSafetyOperation move it. `Mode` stays writable.
- **Life Safety Point 1 and Zone 1 now answer over the wire.** In 1.0.x almost
  every property of both read as unknown-object. Every listed property now reads,
  and a write of `Present_Value` drives the alarm algorithms.
- **Protocol_Revision is 30.** Segmentation is supported in both directions.
- **Device renamed** from the placeholder "Rainbow" to "Chipkin Example B-ALSC", so
  examples in this series can be told apart on one network.
- **Build**: the documented and released build compiles the stack from source with
  two commands (`cmake -B build -S .`, `cmake --build build --config Release`) on
  every platform. `CMakeLists.txt` defines
  `STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION`; a prebuilt static or DLL stack
  library must be built with it.
- **Documentation**: README is now this example only; configuration guidance and
  troubleshooting moved to a new `TUTORIAL.md`; a new `docs/PICS.md` lists the
  objects and properties.
- Vendored `common/` updated to 3.4.0 (see `common/CHANGELOG.md`).
- `APP_VERSION` is 1.2.0.

### Fixed

- **An alarm value of 2 raises LIFE_SAFETY_ALARM** (Event_State life-safety-alarm)
  instead of offnormal.
- **`Local_Date` and `Local_Time` read as values**, which also fixes Schedule 1's
  `Present_Value` (it read value-not-initialized).
- **`Application_Software_Version` and `Firmware_Revision`** now report the running
  build and linked stack version instead of a fixed "1.0.0".
- The README no longer calls Event Log capture of Amber's alarms blocked; it works.

### Compatibility

- Known limitations: Life Safety Zone `Zone_Members` is always empty, and Event
  Log `Enable` starts FALSE. See `TODO.md`.
- Alarms now go to the workstation at Device 389108; change this in Notification
  Class 1 or write `Recipient_List` for your site.

## [1.0.0] - 2026-09-15

First release: a B-ALSC (Advanced Life Safety Controller) example. It carries the
B-LSC example's object model (inputs, outputs, Life Safety Point "Amber", Life
Safety Zone "Azure", Notification Class 1) and adds an Event Log ("Beige", read
with ReadRange) and a Schedule ("Saffron") with a Calendar ("Cream"). Built on CAS
BACnet Stack 6.x (abd4cee1, reports 6.0.21) as a prebuilt static library.

### Added

- Life safety alarm and fault reporting, AcknowledgeAlarm (AE-ACK-B),
  GetEventInformation (AE-INFO-B), COV on Analog Input 1 and Life Safety Point 1
  (DS-COV-B), ReadPropertyMultiple, WritePropertyMultiple,
  DeviceCommunicationControl, ReinitializeDevice, time synchronization and discovery.
- `README.md`, `AGENTS.md`, `TODO.md` and a CMake build.

### Compatibility

- Known limitations in this release: almost every property of Life Safety Point 1
  and Zone 1 answers unknown-object, `Zone_Members` cannot be served,
  LifeSafetyOperation is not enabled in the static library, and the Event Log
  cannot capture the life safety alarms. All are resolved or documented in 1.2.0.
