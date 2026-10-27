#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-ALSC Wire Test - the controller logs its own life-safety alarms in Event Log 1, even when nobody hears them.

    python3 tests/event_log_test.py [--exe build/BACnetExampleBALSC] [--port 47836]

135-2024 L.5.1: "Logging of event notifications of the local device in an Event Log object"
(AE-EL-I-B, K.2.21: "The B device collects the event notifications in an internal buffer";
Log_Buffer is read with ReadRange, cl. 12.27.13). The Peer is a Python workstation that never
announces itself, so Notification Class 1's recipient (Device 389108) cannot be reached.

  1. Event Log 1's Enable at start-up: TRUE is what L.5.1 asks for; the stack starts it FALSE
     and the customer interface cannot set it ([KNOWN GAP], stack #3301).
  2. Control: with Enable FALSE, a detector fault and its repair log nothing (Record_Count 0).
  3. The workstation writes Enable TRUE -> SimpleACK, and Record_Count grows (the log-status
     record).
  4. Smoke. Failure Mode - the recipient is unreachable (Device 389108 never announced itself):
     the point still goes to LIFE_SAFETY_ALARM and GetEventInformation still lists it ...
  5. ... and the Event Log holds the alarm: ReadRange of Log_Buffer returns Record_Count
     records, among them the CHANGE_OF_LIFE_SAFETY notification from Device 389008 for Life
     Safety Point 1 (normal -> LIFE_SAFETY_ALARM), exactly once, and one for Life Safety Zone 1.
  6. ReadRange by position (1, 1) returns exactly one record; Log_Buffer refuses ReadProperty.
"""
import sys

import alsc_setup as setup
from alsc_setup import alarm_codec, wiretest
from wiretest import known_gap, record

ALARM = alarm_codec
LIFE_SAFETY_ALARM = wiretest.alarm.EVENT_STATE_LIFE_SAFETY_ALARM


def describe_records(records):
    return "; ".join(f"{entry['kind']}" + (f" {entry['event_object']} {entry['from_state']}->{entry['to_state']} "
                                            f"from {entry['initiating_device']} process {entry['process_identifier']}"
                                            if entry["kind"] == "notification" else "") for entry in records)


def run(workstation, args):
    # --- 1. Enable at start-up ----------------------------------------------------------
    enable = setup.read(workstation, args, setup.BEIGE, setup.PROPERTY_ENABLE)
    known_gap("Event Log 1 is enabled at start-up, logging without an operator's write first",
              enable is True, f"stack #3301: Enable starts FALSE and the customer interface cannot set it (read {enable})")

    # --- 2. Control: Enable FALSE logs nothing ---------------------------------------------
    count = setup.read(workstation, args, setup.BEIGE, setup.PROPERTY_RECORD_COUNT)
    record("Control: Record_Count starts at 0", count == 0, f"read {count}")
    faulted = setup.detector(args, "fault") == "ok" and wiretest.wait_until(
        lambda: setup.read(workstation, args, setup.AMBER, ALARM.PROPERTY_EVENT_STATE) == ALARM.EVENT_STATE_FAULT, 3)
    repaired = setup.detector(args, "quiet") == "ok" and wiretest.wait_until(
        lambda: setup.read(workstation, args, setup.AMBER, ALARM.PROPERTY_EVENT_STATE) == ALARM.EVENT_STATE_NORMAL, 3)
    record("Control: a detector fault and its repair happen (FAULT, then NORMAL)", faulted and repaired,
           f"fault seen {bool(faulted)}, repair seen {bool(repaired)}")
    count = setup.read(workstation, args, setup.BEIGE, setup.PROPERTY_RECORD_COUNT)
    record("Control: with Enable FALSE they log nothing (Record_Count 0)", count == 0, f"read {count}")

    # --- 3. Enable ----------------------------------------------------------------------------
    answer = setup.write_enable(workstation, args, True)
    record("WriteProperty Enable TRUE -> SimpleACK", answer.ok, answer.describe())
    enabled_count = setup.read(workstation, args, setup.BEIGE, setup.PROPERTY_RECORD_COUNT)
    record("Record_Count grows (the log-status record)", enabled_count is not None and enabled_count >= 1,
           f"read {enabled_count}")

    # --- 4. Smoke, and nobody to tell ---------------------------------------------------------
    record("Failure Mode set-up: the recipient, Device 389108, is not bound (it never announced itself)",
           not setup.is_bound(workstation, args), "Device_Address_Binding")
    reply = setup.detector(args, "smoke")
    record("SIMULATION: the detector sees smoke", reply == "ok", f"reply {reply!r}")
    in_alarm = wiretest.wait_until(
        lambda: setup.read(workstation, args, setup.AMBER, ALARM.PROPERTY_EVENT_STATE) == LIFE_SAFETY_ALARM, 3)
    record("Failure Mode: with the recipient unreachable the point still goes to LIFE_SAFETY_ALARM", in_alarm)
    summaries, _, answer = setup.get_event_information(workstation, args)
    entry = setup.summary_for(summaries, setup.AMBER)
    record("  ... and GetEventInformation still lists it, to-offnormal unacknowledged",
           entry is not None and entry["event_state"] == LIFE_SAFETY_ALARM and
           entry["acked_transitions"][alarm_codec.TO_OFFNORMAL] is False,
           setup.describe_summary(entry) if summaries is not None else answer.describe())

    # --- 5. ... and the Event Log holds it ------------------------------------------------------
    count = wiretest.wait_until(
        lambda: (lambda value: value if value and value > enabled_count else None)(
            setup.read(workstation, args, setup.BEIGE, setup.PROPERTY_RECORD_COUNT)), 3)
    record("Record_Count grows after the alarm", count is not None, f"read {count}, was {enabled_count}")
    log, records, answer = setup.read_event_log(workstation, args)
    record("ReadRange of Log_Buffer -> ReadRange-ACK", log is not None, answer.describe())
    record("ReadRange returns Record_Count records", log is not None and log["item_count"] == count == len(records),
           f"item count {log and log['item_count']}, decoded {len(records)}, Record_Count {count}")
    for name, reference in (("Life Safety Point 1", setup.AMBER), ("Life Safety Zone 1", setup.AZURE)):
        logged = [entry for entry in records if entry["kind"] == "notification" and
                  entry["event_object"] == reference and entry["to_state"] == LIFE_SAFETY_ALARM]
        record(f"The log holds {name}'s alarm: from Device 389008, normal -> LIFE_SAFETY_ALARM",
               len(logged) >= 1 and logged[0]["initiating_device"] == setup.DEVICE and
               logged[0]["from_state"] == ALARM.EVENT_STATE_NORMAL, describe_records(records))
    point_records = [entry for entry in records if entry["kind"] == "notification" and
                     entry["event_object"] == setup.AMBER and entry["to_state"] == LIFE_SAFETY_ALARM]
    # Stack #3957 logs a device's own BROADCAST notification twice (B-AEC-CPP sees it); this
    # example's recipient is a device, not a broadcast, and its alarm is logged once.
    record("The point's alarm is logged exactly once", len(point_records) == 1, f"{len(point_records)} records")

    # --- 6. By position, and not by ReadProperty ----------------------------------------------
    log, records, answer = setup.read_event_log(workstation, args, 1, 1)
    record("ReadRange by position (1, 1) returns exactly one record",
           log is not None and log["item_count"] == 1 and len(records) == 1, answer.describe())
    answer = workstation.read_property(args.port, *setup.BEIGE, setup.PROPERTY_LOG_BUFFER)
    record("Log_Buffer refuses ReadProperty (cl. 12.27.13: read with ReadRange only)",
           answer.error is not None, answer.describe())


def main():
    args = setup.parser(__doc__).parse_args()
    controller = setup.start_controller(args)
    workstation = setup.workstation()
    try:
        run(workstation, args)
    finally:
        workstation.close()
        controller.stop()
        if not all(wiretest.results.RESULTS):
            controller.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
