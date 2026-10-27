#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-ALSC discovery: read every property the advanced life safety controller says it has, the way a client does.

    python3 tests/discovery_test.py [--exe build/BACnetExampleBALSC] [--port 47836]

What a BACnet client such as Chipkin BACnet Explorer does when it discovers a device,
done over the wire from outside the example:

    1. Who-Is   -> the I-Am of Device 389008
    2. ReadProperty Device Object_List
    3. for every object: ReadProperty Property_List, then ReadProperty of every
       property it lists (and of Object_Identifier, Object_Name, Object_Type and
       Property_List itself, which cl. 12.1.1.4.1 leaves out of the list)

Every one of those reads must come back as a value - a ReadProperty ComplexACK. An
Error, Reject or Abort, or no answer, fails the check: Property_List holds "one property
identifier for each property that exists within the object" (135-2024 cl. 12.1.1.4.1),
so a listed property the device cannot read is a defect, whoever owns it.

The one exception is a property the standard says ReadProperty must refuse: Event Log 1's
Log_Buffer "is not network accessible except through the use of the ReadRange service"
(cl. 12.27.13), and a property "not accessible using this service" answers PROPERTY /
READ_ACCESS_DENIED (cl. 15.5.1.3.1). It is checked for exactly that error instead.

The three reads named separately are the ones Explorer 4.23.2.0 found failing on
Network Port 1 at stack 6.0.21 (reported against B-SS-CPP as issues #20, #21, #22;
every example in the series serves the same Network Port).

Exit code 0 = every check passed.
"""
import argparse
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

import wiretest  # noqa: E402  (the vendored harness at the repository root)
from wiretest import record, summary  # noqa: E402

# Match main.cpp.
OBJECT_TYPE_CALENDAR = 6               # cl. 21 BACnetObjectType
OBJECT_TYPE_MULTI_STATE_OUTPUT = 14    # cl. 21 BACnetObjectType
OBJECT_TYPE_NOTIFICATION_CLASS = 15    # cl. 21 BACnetObjectType
OBJECT_TYPE_SCHEDULE = 17              # cl. 21 BACnetObjectType
OBJECT_TYPE_LIFE_SAFETY_POINT = 21     # cl. 21 BACnetObjectType
OBJECT_TYPE_LIFE_SAFETY_ZONE = 22      # cl. 21 BACnetObjectType
OBJECT_TYPE_EVENT_LOG = 25             # cl. 21 BACnetObjectType
DEVICE_INSTANCE = 389008
DEVICE = (wiretest.OBJECT_TYPE_DEVICE, DEVICE_INSTANCE)
NETWORK_PORT = (wiretest.OBJECT_TYPE_NETWORK_PORT, 1)            # Network Port 1 "Vermilion"
EXPECTED_OBJECTS = [DEVICE,
                    (wiretest.OBJECT_TYPE_ANALOG_INPUT, 1),      # "Bronze"
                    (wiretest.OBJECT_TYPE_BINARY_INPUT, 1),      # "Emerald"
                    (wiretest.OBJECT_TYPE_MULTI_STATE_INPUT, 1), # "Hot Pink"
                    (wiretest.OBJECT_TYPE_ANALOG_OUTPUT, 1),     # "Chartreuse"
                    (wiretest.OBJECT_TYPE_BINARY_OUTPUT, 1),     # "Fuchsia"
                    (OBJECT_TYPE_MULTI_STATE_OUTPUT, 1),         # "Indigo"
                    (OBJECT_TYPE_LIFE_SAFETY_POINT, 1),          # "Amber"
                    (OBJECT_TYPE_LIFE_SAFETY_ZONE, 1),           # "Azure"
                    (OBJECT_TYPE_NOTIFICATION_CLASS, 1),         # "Crimson"
                    (OBJECT_TYPE_SCHEDULE, 1),                   # "Saffron"
                    (OBJECT_TYPE_CALENDAR, 1),                   # "Cream"
                    (OBJECT_TYPE_EVENT_LOG, 1),                  # "Beige"
                    NETWORK_PORT]

# Database_Revision (cl. 12.11): the stack starts it at 0 and adds 1 for each object the
# example adds at start-up - the Device and the thirteen objects above - and nothing creates,
# deletes or renames an object afterwards, so it reads 14 for the life of the process
# (docs/PICS.md).
PROPERTY_DATABASE_REVISION = 155
EXPECTED_DATABASE_REVISION = len(EXPECTED_OBJECTS)

# Analog Input 1's COV_Increment (cl. 12.2.16): required because the object supports COV
# reporting (cl. 12.2 footnote 2), as main.cpp serves it.
PROPERTY_COV_INCREMENT = 22
EXPECTED_COV_INCREMENT = 1.0

# Analog Input 1's Out_Of_Service (cl. 12.2.10) is writable, and its Present_Value is
# writable only while Out_Of_Service is TRUE (cl. 12.2.4, Table 12-2 footnote 1).
PROPERTY_OUT_OF_SERVICE = 81
PROPERTY_PRESENT_VALUE = 85
PROPERTY_STATUS_FLAGS = 111
STATUS_FLAG_OUT_OF_SERVICE = 3                     # BACnetStatusFlags bit 3
ERROR_PROPERTY_WRITE_ACCESS_DENIED = (2, 40)
SIMULATED_VALUE = 33.5

# Listed properties ReadProperty must refuse, and the error it must refuse them with
# (see the module docstring): Event Log 1's Log_Buffer, PROPERTY / READ_ACCESS_DENIED.
PROPERTY_LOG_BUFFER = 131
ERROR_PROPERTY_READ_ACCESS_DENIED = (2, 27)
REFUSED_BY_THE_STANDARD = {((OBJECT_TYPE_EVENT_LOG, 1), PROPERTY_LOG_BUFFER): ERROR_PROPERTY_READ_ACCESS_DENIED}

# SubscribeCOV (cl. 13.14): Analog Input 1 "Bronze" is COV-subscribable, and the device
# accepts lifetimes up to 8 hours (main.cpp COV_MAX_SUPPORTED_LIFETIME_SECONDS; the BTL Test
# Plan requires it for DS-COV-B, 135.1 9.10.1.10). One second more is refused.
SERVICE_SUBSCRIBE_COV = 5              # BACnetConfirmedServiceChoice subscribeCOV
COV_PROCESS_IDENTIFIER = 57
COV_MAX_LIFETIME_SECONDS = 8 * 60 * 60

# The four properties cl. 12.1.1.4.1 says Property_List does not contain.
PROPERTY_OBJECT_TYPE = 79
NOT_IN_PROPERTY_LIST = [wiretest.PROPERTY_OBJECT_IDENTIFIER, wiretest.PROPERTY_OBJECT_NAME,
                        PROPERTY_OBJECT_TYPE, wiretest.PROPERTY_PROPERTY_LIST]

# Network Port properties Explorer could not read at stack 6.0.21 (cl. 12.56; numbers from
# cl. 21 BACnetPropertyIdentifier), with the issue that reported each.
PROPERTY_IP_DNS_SERVER = 406
PROPERTY_FD_BBMD_ADDRESS = 418
PROPERTY_FD_SUBSCRIPTION_LIFETIME = 419
EXPLORER_FAILURES = [(PROPERTY_IP_DNS_SERVER, "IP_DNS_Server", "#20"),
                     (PROPERTY_FD_BBMD_ADDRESS, "FD_BBMD_Address", "#21"),
                     (PROPERTY_FD_SUBSCRIPTION_LIFETIME, "FD_Subscription_Lifetime", "#22")]

OBJECT_TYPE_NAMES = {wiretest.OBJECT_TYPE_ANALOG_INPUT: "Analog Input",
                     wiretest.OBJECT_TYPE_ANALOG_OUTPUT: "Analog Output",
                     wiretest.OBJECT_TYPE_BINARY_INPUT: "Binary Input",
                     wiretest.OBJECT_TYPE_BINARY_OUTPUT: "Binary Output", wiretest.OBJECT_TYPE_DEVICE: "Device",
                     wiretest.OBJECT_TYPE_MULTI_STATE_INPUT: "Multi-state Input",
                     OBJECT_TYPE_MULTI_STATE_OUTPUT: "Multi-state Output",
                     wiretest.OBJECT_TYPE_NETWORK_PORT: "Network Port",
                     OBJECT_TYPE_NOTIFICATION_CLASS: "Notification Class",
                     OBJECT_TYPE_LIFE_SAFETY_POINT: "Life Safety Point",
                     OBJECT_TYPE_LIFE_SAFETY_ZONE: "Life Safety Zone", OBJECT_TYPE_SCHEDULE: "Schedule",
                     OBJECT_TYPE_CALENDAR: "Calendar", OBJECT_TYPE_EVENT_LOG: "Event Log"}
PDU_NAMES = {wiretest.PDU_ERROR: "Error", wiretest.PDU_REJECT: "Reject", wiretest.PDU_ABORT: "Abort"}


def parser():
    arguments = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    arguments.add_argument("--exe", default=str(wiretest.default_exe(REPOSITORY, "BACnetExampleBALSC")),
                           help="path to BACnetExampleBALSC (default: build/BACnetExampleBALSC)")
    arguments.add_argument("--port", type=int, default=47836,
                           help="the advanced life safety controller's UDP port (default 47836)")
    return arguments


def object_text(object_identifier):
    object_type, instance = object_identifier
    return f"{OBJECT_TYPE_NAMES.get(object_type, f'object type {object_type}')} {instance}"


def subscribe_cov_request(invoke_id, object_identifier, lifetime=None):
    """SubscribeCOV-Request (cl. 13.14.1): subscriber-process-identifier [0], monitored-object [1],
    and for a subscription issue-confirmed-notifications [2] (FALSE) and lifetime [3]; with
    lifetime=None both are left out, which cancels the subscription."""
    parameters = (wiretest.context_unsigned(0, COV_PROCESS_IDENTIFIER) +
                  wiretest.context_object_id(1, *object_identifier))
    if lifetime is not None:
        parameters += wiretest.context_boolean(2, False) + wiretest.context_unsigned(3, lifetime)
    return wiretest.confirmed_request(invoke_id, SERVICE_SUBSCRIBE_COV, parameters)


def outcome(answer):
    """What a ReadProperty got back, in words: the value, or why there is none."""
    if not answer.answered:
        return "no answer"
    if answer.frame.pdu_type == wiretest.PDU_COMPLEX_ACK:
        return f"value {answer.value!r}"
    if answer.error is not None:
        return f"Error class={answer.error[0]} code={answer.error[1]}"
    if answer.frame.pdu_type in (wiretest.PDU_REJECT, wiretest.PDU_ABORT) and len(answer.frame.payload) > 2:
        return f"{PDU_NAMES[answer.frame.pdu_type]} reason={answer.frame.payload[2]}"
    return answer.describe()


def is_value(answer):
    return answer.answered and answer.frame.pdu_type == wiretest.PDU_COMPLEX_ACK


def who_is(client, port, attempts=2):
    """Who-Is for this one device, unicast to it (a client that already knows the address
    does this; Explorer broadcasts). Returns the I-Am frame that comes back, or None.
    Who-Is is unconfirmed, so nothing else retries it: if no I-Am comes back it is sent
    once more, with a visible [RETRY] line (the example's UDP receive can drop a datagram
    on Windows - common/ SimpleUDP)."""
    for attempt in range(attempts):
        if attempt:
            print("[RETRY] Who-Is got no I-Am in 3.0 s - sent again", flush=True)
        client.frames.clear()
        client.send(wiretest.bvlc(wiretest.npdu(wiretest.who_is(DEVICE_INSTANCE, DEVICE_INSTANCE))), port)
        frame = client.wait_for(lambda candidate: wiretest.i_am_device_instance(candidate.payload) == DEVICE_INSTANCE,
                                3.0)
        if frame is not None:
            return frame
    return None


def main():
    args = parser().parse_args()
    device = wiretest.start(args.exe, ["--port", args.port], "B-ALSC")
    client = wiretest.Client(retries=1)
    try:
        i_am = who_is(client, args.port)
        record(f"Who-Is: Device {DEVICE_INSTANCE} answers with an I-Am", i_am is not None,
               "no I-Am" if i_am is None else "")

        object_list_answer = client.read_property(args.port, *DEVICE, wiretest.PROPERTY_OBJECT_LIST, timeout=2.0)
        object_list = wiretest.decoded_values(object_list_answer.value_octets) if is_value(object_list_answer) else []
        # Control: the walk below proves nothing if it walks nothing.
        record("Device Object_List names the Device, Analog Input 1, Binary Input 1, Multi-state Input 1, "
               "Analog Output 1, Binary Output 1, Multi-state Output 1, Life Safety Point 1, "
               "Life Safety Zone 1, Notification Class 1, Schedule 1, Calendar 1, Event Log 1 and Network Port 1",
               sorted(object_list) == sorted(EXPECTED_OBJECTS),
               f"{len(object_list)} objects" if is_value(object_list_answer) else outcome(object_list_answer))

        reads = 0
        unreadable = {}
        refusals = {}
        property_lists = {}
        for object_identifier in object_list:
            list_answer = client.read_property(args.port, *object_identifier, wiretest.PROPERTY_PROPERTY_LIST,
                                               timeout=2.0)
            property_list = wiretest.decoded_values(list_answer.value_octets) if is_value(list_answer) else []
            property_lists[object_identifier] = property_list
            record(f"{object_text(object_identifier)}: Property_List reads", is_value(list_answer) and property_list,
                   outcome(list_answer) if not is_value(list_answer) else f"{len(property_list)} properties")
            for property_identifier in NOT_IN_PROPERTY_LIST + property_list:
                answer = client.read_property(args.port, *object_identifier, property_identifier, timeout=2.0)
                reads += 1
                if (object_identifier, property_identifier) in REFUSED_BY_THE_STANDARD:
                    refusals[(object_identifier, property_identifier)] = answer
                    continue
                if not is_value(answer):
                    unreadable[(object_identifier, property_identifier)] = outcome(answer)
                    print(f"[UNREADABLE] {object_text(object_identifier)} property {property_identifier}: "
                          f"{outcome(answer)}", flush=True)

        record(f"every property of every object reads as a value ({reads} reads)", reads and not unreadable,
               f"{len(unreadable)} unreadable: " + ", ".join(
                   f"{object_text(object_identifier)} {property_identifier}"
                   for object_identifier, property_identifier in unreadable) if unreadable else "")

        for (object_identifier, property_identifier), expected in REFUSED_BY_THE_STANDARD.items():
            answer = refusals.get((object_identifier, property_identifier))
            record(f"{object_text(object_identifier)} Log_Buffer ({property_identifier}): ReadProperty is refused with "
                   f"PROPERTY / READ_ACCESS_DENIED (cl. 12.27.13, 15.5.1.3.1)",
                   answer is not None and answer.error == expected,
                   "not in Property_List" if answer is None else outcome(answer))

        # The three Explorer reported, by name - listed in Property_List and readable.
        network_port_list = property_lists.get(NETWORK_PORT, [])
        for property_identifier, name, issue in EXPLORER_FAILURES:
            listed = property_identifier in network_port_list
            failure = unreadable.get((NETWORK_PORT, property_identifier))
            record(f"Network Port 1 {name} ({property_identifier}): listed in Property_List and reads as a value "
                   f"(issue {issue})", listed and failure is None,
                   "not in Property_List" if not listed else (failure or ""))

        database_revision = client.read_property(args.port, *DEVICE, PROPERTY_DATABASE_REVISION, timeout=2.0)
        record(f"Device Database_Revision reads {EXPECTED_DATABASE_REVISION}, one per object added at start-up "
               "(docs/PICS.md)", is_value(database_revision) and database_revision.value == EXPECTED_DATABASE_REVISION,
               outcome(database_revision))

        bronze = (wiretest.OBJECT_TYPE_ANALOG_INPUT, 1)
        record("Analog Input 1 lists COV_Increment in its Property_List (it supports COV reporting, "
               "cl. 12.2 footnote 2)", PROPERTY_COV_INCREMENT in property_lists.get(bronze, []))
        cov_increment = client.read_property(args.port, *bronze, PROPERTY_COV_INCREMENT, timeout=2.0)
        record(f"Analog Input 1 COV_Increment reads {EXPECTED_COV_INCREMENT}",
               is_value(cov_increment) and cov_increment.value == EXPECTED_COV_INCREMENT, outcome(cov_increment))
        eight_hours = client.request(lambda invoke_id: subscribe_cov_request(
            invoke_id, bronze, COV_MAX_LIFETIME_SECONDS), args.port)
        record("SubscribeCOV on Analog Input 1 with an 8-hour lifetime (28800 s) is accepted (DS-COV-B)",
               eight_hours.acked, outcome(eight_hours))
        too_long = client.request(lambda invoke_id: subscribe_cov_request(
            invoke_id, bronze, COV_MAX_LIFETIME_SECONDS + 1), args.port)
        record("SubscribeCOV with a lifetime one second over 8 hours is refused",
               too_long.error is not None, outcome(too_long))
        cancelled = client.request(lambda invoke_id: subscribe_cov_request(invoke_id, bronze), args.port)
        record("SubscribeCOV cancellation (no lifetime) is accepted", cancelled.acked, outcome(cancelled))

        # Out_Of_Service (cl. 12.2.10): in service, Present_Value is the sensor's and a write is refused.
        sensor = client.read_property(args.port, *bronze, PROPERTY_PRESENT_VALUE, timeout=2.0)
        refused = client.write_property(args.port, *bronze, PROPERTY_PRESENT_VALUE,
                                        wiretest.application_real(SIMULATED_VALUE), timeout=2.0)
        record("Analog Input 1 in service: a write of Present_Value is refused (PROPERTY / WRITE_ACCESS_DENIED)",
               refused.error == ERROR_PROPERTY_WRITE_ACCESS_DENIED, outcome(refused))
        out = client.write_property(args.port, *bronze, PROPERTY_OUT_OF_SERVICE,
                                    wiretest.application_boolean(True), timeout=2.0)
        record("Analog Input 1: Out_Of_Service is writable (TRUE accepted)", out.acked, outcome(out))
        out_read = client.read_property(args.port, *bronze, PROPERTY_OUT_OF_SERVICE, timeout=2.0)
        record("Analog Input 1: Out_Of_Service reads TRUE", is_value(out_read) and out_read.value is True,
               outcome(out_read))
        flags = client.read_property(args.port, *bronze, PROPERTY_STATUS_FLAGS, timeout=2.0)
        record("Analog Input 1 out of service: Status_Flags OUT_OF_SERVICE is set",
               is_value(flags) and len(flags.value) > STATUS_FLAG_OUT_OF_SERVICE
               and flags.value[STATUS_FLAG_OUT_OF_SERVICE] is True, outcome(flags))
        simulated = client.write_property(args.port, *bronze, PROPERTY_PRESENT_VALUE,
                                          wiretest.application_real(SIMULATED_VALUE), timeout=2.0)
        record("Analog Input 1 out of service: a write of Present_Value is accepted", simulated.acked,
               outcome(simulated))
        held = client.read_property(args.port, *bronze, PROPERTY_PRESENT_VALUE, timeout=2.0)
        record(f"Analog Input 1 out of service: Present_Value reads the written {SIMULATED_VALUE}",
               is_value(held) and held.value == SIMULATED_VALUE, outcome(held))
        back = client.write_property(args.port, *bronze, PROPERTY_OUT_OF_SERVICE,
                                     wiretest.application_boolean(False), timeout=2.0)
        record("Analog Input 1: Out_Of_Service FALSE is accepted", back.acked, outcome(back))
        restored = client.read_property(args.port, *bronze, PROPERTY_PRESENT_VALUE, timeout=2.0)
        record("Analog Input 1 back in service: Present_Value is the sensor's again",
               is_value(restored) and is_value(sensor) and restored.value == sensor.value, outcome(restored))
        refused_again = client.write_property(args.port, *bronze, PROPERTY_PRESENT_VALUE,
                                              wiretest.application_real(SIMULATED_VALUE), timeout=2.0)
        record("Analog Input 1 back in service: a write of Present_Value is refused again",
               refused_again.error == ERROR_PROPERTY_WRITE_ACCESS_DENIED, outcome(refused_again))
    finally:
        client.close()
        device.stop()
    return summary()


if __name__ == "__main__":
    sys.exit(main())
