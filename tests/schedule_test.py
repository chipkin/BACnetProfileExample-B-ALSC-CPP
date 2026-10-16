#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-ALSC Wire Test - the workstation sets the controller's clock, and the local schedule follows it.

    python3 tests/schedule_test.py [--exe build/BACnetExampleBALSC] [--port 47821]

135-2024 L.5.1: "Ability to schedule actions in the local device for binary, analog, and
enumerated values, based on date and time" (SCHED-I-B) and "Ability to synchronize its internal
clock upon request" (DM-TS-B). The controller's Schedule 1 "Saffron" writes Analog Output 1
"Chartreuse" at priority 8: 75.0 from Monday 08:00, Schedule_Default 20.0 otherwise, and 5.0 all day on every date in
Calendar 1 "Cream" (Date_List: December 25, any year). The workstation moves the
controller's clock with TimeSynchronization (cl. 16.7) and reads what follows.

  1. Control: before any sync, Local_Date is today's date on this host.
  2. TimeSynchronization 2026-12-25 10:00 -> Local_Date 2026-12-25; Cream TRUE; Saffron
     5.0; Chartreuse 5.0 with Priority_Array[8] = 5.0 (the schedule wrote it).
  3. TimeSynchronization Monday 2026-10-19 09:00 -> Cream FALSE; Saffron and Chartreuse 75.0.
  4. TimeSynchronization Monday 2026-10-19 07:00 -> before the 08:00 transition: 20.0.
"""
import datetime
import sys
import time

import alsc_setup as setup
from alsc_setup import Workstation, alarm_codec, wiretest
from wiretest import PROPERTY_PRESENT_VALUE, PROPERTY_PRIORITY_ARRAY, record

SETTLE = 1.5    # seconds for the controller to apply the sync and tick the schedule


def synchronize(workstation, args, moment):
    workstation.send_unconfirmed(alarm_codec.time_synchronization(
        moment.year, moment.month, moment.day, moment.isoweekday(), moment.hour, moment.minute, moment.second),
        args.port)
    time.sleep(SETTLE)


def local_date(workstation, args):
    """Device Local_Date as a datetime.date, or None."""
    octets = workstation.read_property(args.port, *setup.DEVICE, alarm_codec.PROPERTY_LOCAL_DATE).value_octets
    if octets is None or len(octets) != 5:
        return None
    return datetime.date(1900 + octets[1], octets[2], octets[3])


def schedule_state(workstation, args):
    return (setup.read(workstation, args, setup.CREAM, PROPERTY_PRESENT_VALUE),
            setup.read(workstation, args, setup.SAFFRON, PROPERTY_PRESENT_VALUE),
            setup.read(workstation, args, setup.CHARTREUSE, PROPERTY_PRESENT_VALUE),
            setup.read(workstation, args, setup.CHARTREUSE, PROPERTY_PRIORITY_ARRAY, setup.SCHEDULE_WRITE_PRIORITY))


def run(workstation, args):
    before = local_date(workstation, args)
    today = datetime.date.today()
    record("Control: before any sync, Local_Date is this host's date",
           before in (today, today - datetime.timedelta(days=1), today + datetime.timedelta(days=1)),
           f"read {before}, host {today}")

    christmas = datetime.datetime(2026, 12, 25, 10, 0, 0)
    synchronize(workstation, args, christmas)
    synced = local_date(workstation, args)
    record("TimeSynchronization 2026-12-25 10:00: Local_Date reads 2026-12-25", synced == christmas.date(),
           f"read {synced}")
    state = schedule_state(workstation, args)
    record("On a Calendar date: Cream TRUE, Saffron 5.0, Chartreuse 5.0 with Priority_Array[8] 5.0",
           state == (True, setup.SCHEDULE_EXCEPTION_VALUE, setup.SCHEDULE_EXCEPTION_VALUE,
                     setup.SCHEDULE_EXCEPTION_VALUE),
           f"read (Cream, Saffron, Chartreuse, Priority_Array[8]) {state}")

    monday_nine = datetime.datetime(2026, 10, 19, 9, 0, 0)
    synchronize(workstation, args, monday_nine)
    state = schedule_state(workstation, args)
    record("Monday 2026-10-19 09:00: Cream FALSE, Saffron and Chartreuse 75.0 (the 08:00 transition)",
           state == (False, setup.SCHEDULE_WEEKLY_VALUE, setup.SCHEDULE_WEEKLY_VALUE, setup.SCHEDULE_WEEKLY_VALUE),
           f"read {state}")

    monday_seven = datetime.datetime(2026, 10, 19, 7, 0, 0)
    synchronize(workstation, args, monday_seven)
    state = schedule_state(workstation, args)
    record("Monday 2026-10-19 07:00: before the transition, Schedule_Default 20.0",
           state == (False, setup.SCHEDULE_DEFAULT_VALUE, setup.SCHEDULE_DEFAULT_VALUE, setup.SCHEDULE_DEFAULT_VALUE),
           f"read {state}")


def main():
    args = setup.parser(__doc__).parse_args()
    controller = setup.start_controller(args)
    workstation = Workstation()
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
