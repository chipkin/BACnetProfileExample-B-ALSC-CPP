# VeriBACnet results

The latest VeriBACnet run of this folder's project, summarised by hand from
that run's `report.json`. The run's own Results Folder (reports, packet
captures, wire logs) is not published: it holds the testing machine's network
addresses.

| | |
|---|---|
| Date | 2026-10-27 |
| Example | BACnet B-ALSC (Advanced Life Safety Controller) Example - C++ v1.2.0 (`common/` 3.5.0), CAS BACnet Stack `6.x` @ `69b6249f` |
| Profile | B-ALSC (BACnet Advanced Life Safety Controller) |
| Transport | BACnet/IP, UDP port 47836 |
| VeriBACnet | 0.20.0 (its test device uses CAS BACnet Stack 6.0.23.0) |
| Test plan | 244 BTL tests (ANSI/ASHRAE 135.1-2023) selected for the B-ALSC profile |
| Result | **100 PASS · 1 FAIL · 0 ERROR · 143 SKIP** |

**Judged BTL-clean on BACnet/IP, with a star**: no failure or error is the
example's own fault, the one failure is tracked, and every skipped test has a
stated reason. The star means some of the functions the example exists for
were not measured by VeriBACnet in this run (below). See "What BTL-clean means"
in [README.md](README.md). This is not BTL certification.

**What changed since the last run:**
- Analog Input 1 can now be taken out of service. Out_Of_Service is writable,
  and while it is TRUE the Present_Value is decoupled from the sensor and
  writable (a write in service is still refused). A client can therefore
  simulate a reading, and the COV notification tests that need a value change
  (8.2.1, 8.2.2, 8.3.1, 8.3.2) now run and pass. The example's Wire Tests check
  the write, read-back and refusal cycle.
- The test tool was updated: its COV, write and Network Port scripts now use
  the device's own objects, so 9.22.1.5, 9.23.1.3, 9.23.1.8, 9.23.2.3 and
  9.23.2.15 pass, as do 7.2.2 and 9.22.2.1.

**Measured coverage:** 101 of the 244 selected tests ran (100 passed, 1
failed). Of the 143 skipped, 86 wait on a test-tool or test-script fix
(tracked; 62 are scenarios the tool cannot yet set up on a device it did not
build, mostly Schedule, Calendar, Event Log and Notification Class, and 12 are
AcknowledgeAlarm tests). 27 need an operator: this device's alarms come from a
simulated smoke detector, which only an operator can trigger. 30 do not apply
to this device: no Trend Log or Event Enrollment, and it neither creates nor
deletes objects. Its Protocol_Revision (30) is outside the Revision 0-19 and
0-3 test forms, and it refuses the deprecated DeviceCommunicationControl
DISABLE option, as that revision requires. Nothing was skipped for other
reasons.

**Measured now:**
- ReadProperty and ReadPropertyMultiple: all 25 tests passed.
- COV subscriptions and notifications on Analog Input 1 (DS-COV-B): the
  subscription, notification, 8-hour lifetime, update and error tests passed,
  as did the Out_Of_Service and Status_Flags notification tests.
- WriteProperty and WritePropertyMultiple: the writes by data type, the
  non-commandable writes, the error tests and command prioritization passed.
- Who-Is and Who-Has: 24 of 26 passed; the other 2 need an operator.
- TimeSynchronization and UTCTimeSynchronization (DM-TS-B and DM-UTC-B).
- ReinitializeDevice: every unsupported state was refused with an error.
- GetEventInformation with no active events.
- ReadRange of Event Log 1's records, by position.
- The Read Support and EPICS consistency tests.
- The Multi-state Input's State_Text and Number_Of_States.
- Two of the life-safety operation error tests: an operation on an object that
  does not support it, and the object-does-not-exist error.

**Not measured yet** (all of it tracked):
- The life-safety operations themselves, reset and silence (AE-LS-B). Those
  tests need an operator, or name a Life Safety Zone 2 this device does not
  have.
- Alarm acknowledgement (AE-ACK-B). The tests find the alarm objects, but need
  an operator to put them back to normal first, or alarm values the project
  does not yet declare.
- Scheduling (SCHED-I-B). The tool cannot yet be given, or set up, the
  Schedule and Calendar scenarios.
- DeviceCommunicationControl disable-initiation (DM-DCC-B). The tests pick
  Analog Output 1 as the object to change, which is not offered for COV, and do
  not use Analog Input 1, which is (tracked).
- Who-Is initiation (DM-DDB-A). This example sends a Who-Is on its own only at
  start-up, so the test needs an operator.

This example's own Wire Tests cover these functions end to end. Smoke latches
the alarm. The confirmed alarm reaches the recipients in the writable recipient
list and is logged in the Event Log (read back with ReadRange). It is silenced,
acknowledged and reset, and a reset while the smoke is still there is refused.
A detector fault is reported and cleared. The Schedule follows the clock a
TimeSynchronization sets.

## Tests that did not pass

| Test | Result | Why |
|---|---|---|
| 9.9.2.2 LifeSafetyOperation which is Invalid given the Object's Current State | FAIL | The script sends the operation to Life Safety Point 3, which this device does not have, so the device correctly answers "unknown object". This device does refuse operations that are invalid in the current state (its Wire Tests show it). A test-script defect. |

## Skipped tests, by reason

| Tests | Why |
|---|---|
| 62 scenarios the tool cannot yet set up | Schedule and Calendar (7.3.2.23.x, 7.3.2.8.x, 7.2.4, 7.2.10, 7.2.11), Event Log logging scenarios and ReadRange by time and sequence number (7.3.2.24.x, 9.21.x), Notification Class recipients (7.3.2.21.3.x), and Life Safety Point fixtures (7.3.2.15.x, 9.9.1.2). The scripts need scenarios the project cannot describe for this device yet. Tracked. |
| 9.1.1.8 to 9.1.1.11, 9.1.1.15, 9.1.2.x and 7.3.1.11.1 AcknowledgeAlarm (12) | The tests compare against expected alarm values the project does not yet declare. They need the alarm raised by an operator in any case. Tracked. |
| 9.10.1.4, .5, .7, .9, .11 and 9.24.1.6 to .10, .12 COV and DeviceCommunicationControl (11) | The tests choose Analog Output 1 as the object to change, and the device correctly refuses a COV subscription on it. Analog Input 1 offers COV and can be changed through Out_Of_Service, but the tests do not use it. Tracked. |
| 8.2.3 COV notification without a COV_Increment | The test's own receive step missed the first notification: the device sent it 5 ms after the subscription was acknowledged, and the test tool acknowledged it. Tracked. |
| 27 tests that need an operator | The run was unattended. They cover the life-safety reset and silence, the alarm acknowledgement baseline (9.1.1.x) and the event reporting sequences (7.3.1.19.x, 7.3.1.20.x, 7.3.1.22.x). They also cover Who-Is initiation (8.34.2), ReinitializeDevice restarts, and changing the Device's name, identifier or UTC offset, which this example takes only at start-up (`--deviceName`, `--deviceID`). |
| 30 tests that do not apply | This device has no Trend Log or Event Enrollment, and it neither creates, deletes nor renames objects (its Database_Revision stays 14). At Protocol_Revision 30 the Revision 0-19 and 0-3 test forms do not apply (including 9.24.1.2 to .5). It rejects the deprecated DeviceCommunicationControl DISABLE option. |

Seven B-ALSC requirements have no VeriBACnet test script yet, so they were not
run: 7.3.1.11.3 and 7.3.1.11.4 Acked_Transitions tests, 7.3.2.23.15
Write_Every_Scheduled_Action FALSE, 8.4 and 8.5 event notification initiation
tests (8.4 twice), and 9.9.2.4 LifeSafetyOperation with a request value the
object does not support.

DeviceCommunicationControl and ReinitializeDevice were tested without a
password: the example ships with none set (its password is a source constant,
empty, not a command-line option).

No public issue has been opened for any of these.
