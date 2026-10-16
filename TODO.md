# TODO - B-ALSC known gaps

This example is **Profile-functional** (series bar, `docs/GLOSSARY.md` in the
examples-series folder): it performs the B-ALSC Profile Function against a Peer, shows
its Failure Modes, and proves both with Wire Tests (`tests/`). B-ALSC is B-LSC plus an
Event Log, internal scheduling and a configurable recipient list; this example is
`BACnetProfileExample-B-LSC-CPP` plus those, and items 1-2 are the same as B-LSC's. The
items below are what it still does not do, why, and what it would take. Re-check every
entry whenever the Stack Pin moves. Checked at stack `6.x` @ `64b2cfac5` (6.0.23),
2026-10-16.

## 1. Life Safety Zone 1 (Azure) Zone_Members cannot be set [KNOWN GAP]

`Zone_Members` (cl. 12.16.26, required, a `BACnetLIST of BACnetDeviceObjectReference`)
"shall indicate which Life Safety Point and Life Safety Zone objects are members of the
zone". `main.cpp` rolls Life Safety Point 1 (Amber) up into Azure, so Zone_Members should
name Amber - but it reads as an **empty list**: the stack serves it, and the only way to
fill it is `BACnetStackTestTool_SetLifeSafetyZoneMembers` in `CASBACnetStackTestToolDLL.h`,
which this series may not use.

**Evidence:** `tests/life_safety_test.py` reports
`[KNOWN GAP] Life Safety Zone 1's Zone_Members lists Life Safety Point 1, the member it
rolls up - stack #2036 ...` on every run.

**Blocked on** [chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036)
(open; owner-approved as a customer-interface addition under tracking issue #2159).

## 2. The stack's own life-safety engine is not used

As B-LSC's TODO.md item 2: the stack's Life Safety Point/Zone engine is not exported
(#2036), so this example holds Amber's and Azure's state itself and applies the latching,
silencing and reset rules in its own callbacks; `Mode` is accepted without an
`Accepted_Modes` check, and a Mode change does not run the algorithm's pMode transition.

## 3. Event Log 1 starts disabled [KNOWN GAP]

`Enable` (cl. 12.27.8) defaults to FALSE and `BACnetStack_AddEventLogObject` takes no
enable argument; the customer header has nothing else that sets it. So Beige logs
**nothing** until a client writes `Enable` TRUE - L.5.1's "Logging of event notifications
of the local device in an Event Log object" needs an operator's write first.

**Evidence:** `tests/event_log_test.py` reports `[KNOWN GAP] Event Log 1 is enabled at
start-up ...` (reads FALSE) and checks, as a control, that a fault and its repair log
nothing while it is FALSE.

**Blocked on** [chipkin/cas-bacnet-stack#3301](https://github.com/chipkin/cas-bacnet-stack/issues/3301)
(open; also found by B-AEC-CPP).

Note: B-AEC-CPP sees each of its own notifications logged twice (stack #3957: the device
logs its own BROADCAST notification again when it hears it). This example's recipients are
a device or an address, never a broadcast, and `tests/event_log_test.py` checks each alarm
is logged exactly once.

## 4. Not Wire-Tested

- **COV** (DS-COV-B): Amber's and Bronze's `Present_Value` are subscribable, but no Wire
  Test subscribes.
- **A silent recipient**: `Number_Of_APDU_Retries` is 3 and checked, but no test counts
  retransmissions (B-AAC-CPP's `silent_recipient_test.py` does).
- **UNSILENCE**, the audible/visual-only operations, and the `s` key's demo schedule entry.

## Done in 1.2.0 (was open in 1.1.0)

- LifeSafetyOperation is compiled in (`STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION`, the
  stack's documented public toggle, in `CMakeLists.txt`) and enabled.
- A simulated smoke detector raises the alarm; `Present_Value` is read-only again.
- Alarms go, confirmed, to Device 389108; Crimson's `Recipient_List` is writable and a
  Wire Test redirects it ("event distribution by another device", L.5.1).
- The Event Log's capture of a real alarm is read back with ReadRange.
- Calendar 1 is stack-held (`BACnetStack_AddCalendarObject`, December 25); the Schedule's
  exception references it; TimeSynchronization sets the device clock the Schedule runs on
  (B-AAC-CPP's canonical pattern), and a Wire Test drives it headless (no `s` key).
- AcknowledgeAlarm and GetEventInformation are exercised end to end.
