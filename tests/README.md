# B-ALSC Wire Tests

Tests that drive the running advanced life safety controller over BACnet/IP from outside
it, and fail when its Profile Function is removed (135-2024 L.5.1: "A B-ALSC device
performs life safety alarm detection and control. It supports life safety objects and
limited modification of its alarm and event reporting, including event distribution by
another device. Also, the device supports scheduling of internal values and event
logging.").

The tests are written against the series' shared harness in
[`../wiretest/`](../wiretest/README.md) (vendored, like `common/`); everything
specific to this example is here. Python 3 standard library only - nothing to
`pip install`.

## Running

Build the example (README "Build"), then from the repository root:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBALSC
```

On Windows, `--exe build\Release\BACnetExampleBALSC.exe`. It ends with
`ALL WIRE TESTS PASSED` (exit 0) or the scripts that failed. `--port` (default
47821) is the UDP port the test starts the example on; the test control channel
uses `--port` + 1. It takes about a minute. CI (`.github/workflows/release.yml`)
runs it on Linux after the smoke test.

A request that gets no answer at all is sent once more with a visible `[RETRY]`
line (the workstation is `wiretest.Workstation(retries=1)`): a busy Windows host drops about 3 UDP
datagrams in 1000. An Error or Reject is an answer and is never retried.

## The setup

```
Workstation (127.0.0.1, ephemeral UDP port)  - the Peer: a Python operator workstation,
    |  BACnet/IP, unicast both ways             Device 389108 (announced with an I-Am)
BACnetExampleBALSC  UDP --port               - Device 389008
    |  loopback test control channel, UDP --port + 1 (BALSC_SIMULATION_CONTROL_PORT)
the SIMULATED smoke detector (main.cpp section 1b)
```

The Peer is `wiretest.Workstation`: a client that is also an event-notification
recipient. Notification Class 1 names it by **device instance** at start-up, so it
sends the panel an I-Am and waits until `Device_Address_Binding` lists Device 389108.
The **test control channel** (`simulation/SimulationControl.h`) plays the physical
world: `detector smoke`, `detector quiet`, `detector fault`.

| File | What it is |
|---|---|
| `alsc_setup.py` | This controller's numbers, starting it with the control channel, the requests the tests send. |
| `discovery_test.py` | Every listed property reads; `Log_Buffer` is refused. |
| `life_safety_test.py`, `fault_test.py` | B-LSC-CPP's two tests with this device's numbers: the life-safety scenario and the detector fault. |
| `event_log_test.py` | AE-EL-I-B: the alarm is logged, even when nobody hears it. |
| `distribution_test.py` | Event distribution by another device. |
| `schedule_test.py` | SCHED-I-B + DM-TS-B (B-AAC-CPP's test with this device's numbers). |

## `life_safety_test.py` and `fault_test.py`

The same checks as B-LSC-CPP's (its `tests/README.md` lists them step by step):
smoke -> latched alarm -> ConfirmedEventNotifications to Device 389108 (and not to a
stranger) -> GetEventInformation -> RESET refused while the smoke is there -> SILENCE
-> AcknowledgeAlarm + ACK_NOTIFICATION -> the smoke clears, the latch holds -> RESET ->
return to normal; RESET of an unlatched point refused; an unacknowledged alarm stays
listed; Zone_Members `[KNOWN GAP]`. And a detector fault -> Reliability
`MULTI_STATE_FAULT`, FAULT, to-fault notification, `RESET_FAULT` refused, repair.

## `event_log_test.py` - every alarm is logged

1. `Enable` at start-up should be TRUE (L.5.1): `[KNOWN GAP]`, stack #3301 - it starts FALSE.
2. **Control**: Record_Count 0; a detector fault and its repair happen and log nothing
   while `Enable` is FALSE.
3. WriteProperty `Enable` TRUE -> SimpleACK; Record_Count grows (the log-status record).
4. **Failure Mode - the recipient is unreachable**: Device 389108 is not bound (no
   workstation announced). Smoke: the point still goes to `LIFE_SAFETY_ALARM` and
   GetEventInformation still lists it ...
5. ... and the log holds it: Record_Count grows; ReadRange of `Log_Buffer` returns
   Record_Count records, among them the `CHANGE_OF_LIFE_SAFETY` notification from Device
   389008 for Life Safety Point 1 (normal -> `LIFE_SAFETY_ALARM`), exactly once, and one
   for Life Safety Zone 1.
6. ReadRange by position (1, 1) returns one record; ReadProperty of `Log_Buffer` is refused.

## `distribution_test.py` - another device redirects the alarms

1. Crimson's `Recipient_List` reads back with the start-up recipient, Device 389108.
2. Workstation A announces itself as Device 389108 and is bound.
3. Workstation B writes `Recipient_List` with itself (address, confirmed, process 9) ->
   SimpleACK; it reads back with B's B/IP address and without Device 389108.
4. Smoke: B receives the life-safety alarm for process 9; A - bound, but no longer on the
   list - receives nothing (the control).

## `schedule_test.py` - the clock and the schedule

1. **Control**: before any sync, `Local_Date` is this host's date.
2. TimeSynchronization 2026-12-25 10:00 -> `Local_Date` 2026-12-25; Cream TRUE; Saffron
   5.0; Chartreuse 5.0 with `Priority_Array[8]` 5.0 (the schedule wrote it).
3. TimeSynchronization Monday 2026-10-19 09:00 -> Cream FALSE; Saffron and Chartreuse 75.0.
4. TimeSynchronization Monday 2026-10-19 07:00 -> before the 08:00 transition: 20.0.

## `discovery_test.py` - every listed property reads as a value

1. **Who-Is** (for 389008, unicast) -> the device's I-Am.
2. **Device `Object_List`** names exactly the Device, Analog Input 1, Binary Input 1,
   Multi-state Input 1, Analog Output 1, Binary Output 1, Multi-state Output 1,
   Life Safety Point 1, Life Safety Zone 1, Notification Class 1, Schedule 1,
   Calendar 1, Event Log 1 and Network Port 1. This is the control: a walk
   over nothing would pass.
3. For each object, **`Property_List`** reads, and a ReadProperty of every
   property it lists - plus `Object_Identifier`, `Object_Name`, `Object_Type`
   and `Property_List`, which cl. 12.1.1.4.1 leaves out of the list - returns a
   ComplexACK. An Error, Reject, Abort or no answer prints an `[UNREADABLE]` line
   and fails the check.
4. Network Port 1's **`IP_DNS_Server` (406)**, **`FD_BBMD_Address` (418)** and
   **`FD_Subscription_Lifetime` (419)** are each listed and read as a value.
5. Event Log 1's **`Log_Buffer` (131)** is the one listed property ReadProperty
   must refuse (cl. 12.27.13), with PROPERTY / READ_ACCESS_DENIED (cl. 15.5.1.3.1).

## Results

Run 2026-10-16, stack `6.x` @ `64b2cfac5` (6.0.23), example v1.2.0:

| Platform | Build | Result |
|---|---|---|
| Windows 11 | STATIC (stack `ReleaseLib` `x64` built with `STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION`, VS 18, NMake) | 21 + 37 + 13 + 17 + 7 + 5 = 100/100, 2 known gaps - PASS x3 (one visible `[RETRY]` in runs 2 and 3) |
| Linux (WSL Ubuntu 22.04) | SOURCE (g++) | 100/100, 2 known gaps - PASS x3, no `[RETRY]` |

Every check was mutation-verified: each of 19 mutations of `main.cpp` (B-LSC-CPP's 13, plus
Recipient_List read-only, Event Log Enable read-only, ReadRange disabled, the Calendar date
moved, the time sync not applied, the weekly transition moved) makes at least one check
fail; the failure lines are in the commit message.
