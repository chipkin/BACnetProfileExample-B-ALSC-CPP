#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-ALSC Wire Test - another device redirects where the life-safety alarms go.

    python3 tests/distribution_test.py [--exe build/BACnetExampleBALSC] [--port 47821]

135-2024 L.5.1: a B-ALSC "supports ... limited modification of its alarm and event reporting,
including event distribution by another device" - "Adjustment of alarm / event parameters
including notification distribution". (A B-LSC is "not required to" - that is the difference.)
Notification Class 1's Recipient_List names Device 389108 at start-up; a second workstation
rewrites it.

  1. Recipient_List reads back with the start-up recipient, Device 389108.
  2. Workstation A announces itself as Device 389108 and is bound.
  3. Workstation B (not 389108) writes Recipient_List with itself, by address, confirmed,
     process 9 -> SimpleACK; it reads back with B's B/IP address.
  4. Smoke: B receives the life-safety alarm (process 9); A - bound, but no longer on the list
     - receives nothing. Where the alarm goes is decided by the list, not by anything else.
"""
import struct
import sys

import alsc_setup as setup
from alsc_setup import Workstation, alarm_codec, extras, wiretest
from wiretest import record

ALARM = alarm_codec
LIFE_SAFETY_ALARM = extras.EVENT_STATE_LIFE_SAFETY_ALARM
SECOND_PROCESS_IDENTIFIER = 9


def run(first, second, args):
    # --- 1. The start-up list --------------------------------------------------------------
    answer = first.read_property(args.port, *setup.CRIMSON, ALARM.PROPERTY_RECIPIENT_LIST)
    workstation_identifier = struct.pack(">I", (wiretest.OBJECT_TYPE_DEVICE << 22) | setup.WORKSTATION_DEVICE_INSTANCE)
    record("Recipient_List reads back with the start-up recipient, Device 389108",
           answer.value_octets is not None and workstation_identifier in answer.value_octets, answer.describe())

    # --- 2. Workstation A is Device 389108 ---------------------------------------------------
    record("Workstation A (Device 389108) is bound", setup.announce(first, args), "Device_Address_Binding")

    # --- 3. Workstation B takes over the list -------------------------------------------------
    answer = setup.write_recipient_list(second, args, ALARM.destination(second.mac, SECOND_PROCESS_IDENTIFIER, True))
    record("Workstation B writes Recipient_List with itself (address, confirmed, process 9) -> SimpleACK",
           answer.ok, answer.describe())
    answer = second.read_property(args.port, *setup.CRIMSON, ALARM.PROPERTY_RECIPIENT_LIST)
    record("Recipient_List reads back with B's B/IP address and no longer names Device 389108",
           answer.value_octets is not None and second.mac in answer.value_octets and
           workstation_identifier not in answer.value_octets, answer.describe())

    # --- 4. The next alarm follows the list ----------------------------------------------------
    first_mark = first.mark()
    reply = setup.detector(args, "smoke")
    record("SIMULATION: the detector sees smoke", reply == "ok", f"reply {reply!r}")
    redirected = second.wait_for_notification(
        setup.notification_from(setup.AMBER, ALARM.NOTIFY_TYPE_ALARM, LIFE_SAFETY_ALARM), setup.NOTIFICATION_WAIT)
    record("Workstation B receives the life-safety alarm, confirmed, for process 9",
           redirected is not None and redirected.confirmed and
           redirected.process_identifier == SECOND_PROCESS_IDENTIFIER, setup.waited(redirected))
    stray = first.wait_for_notification(lambda notification: True, setup.QUIET_WAIT, first_mark)
    record("Control: workstation A, bound but no longer on the list, receives nothing", stray is None,
           setup.waited(stray, setup.QUIET_WAIT))


def main():
    args = setup.parser(__doc__).parse_args()
    controller = setup.start_controller(args)
    first = Workstation()
    second = Workstation()
    try:
        run(first, second, args)
    finally:
        second.close()
        first.close()
        controller.stop()
        if not all(wiretest.results.RESULTS):
            controller.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
