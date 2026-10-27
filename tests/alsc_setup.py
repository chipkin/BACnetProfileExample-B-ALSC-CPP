# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""What B-ALSC's Profile Function Wire Tests share: this controller's numbers, and starting it.

The setup, all on one host:

    Workstation (127.0.0.1, ephemeral UDP port) - the Peer: a Python operator workstation,
        |  BACnet/IP, unicast both ways       Device 389108 (it announces itself with an I-Am)
    BACnetExampleBALSC   UDP --port   Device 389008
        |  loopback test control channel, UDP --port + 1 (BALSC_SIMULATION_CONTROL_PORT)
    the SIMULATED smoke detector inside the example (main.cpp section 1b)

The Peer plays the head-end on a real fire alarm system (a B-OWS): the panel's Notification
Class 1 names it by device instance at start-up (another workstation may rewrite that list -
"event distribution by another device", L.5.1), it receives the life-safety alarms, silences,
acknowledges and resets them, reads the Event Log, and sets the panel's clock. The test control channel plays the physical world - smoke in front of the
detector, its head pulled off the base - and nothing on the BACnet side can do that.
"""
import argparse
import sys
import time
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPOSITORY = TESTS.parent
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(TESTS))

import wiretest  # noqa: E402  (the vendored harness at the repository root)
from wiretest import Workstation  # noqa: E402  (wiretest 0.6.0)
from wiretest import alarm as alarm_codec  # noqa: E402

# Match main.cpp.
DEVICE_INSTANCE = 389008
DEVICE = (wiretest.OBJECT_TYPE_DEVICE, DEVICE_INSTANCE)
OBJECT_TYPE_LIFE_SAFETY_POINT = 21
OBJECT_TYPE_LIFE_SAFETY_ZONE = 22
OBJECT_TYPE_NOTIFICATION_CLASS = 15
AMBER = (OBJECT_TYPE_LIFE_SAFETY_POINT, 1)            # Life Safety Point 1, the smoke detector
AZURE = (OBJECT_TYPE_LIFE_SAFETY_ZONE, 1)             # Life Safety Zone 1, the detector's zone
CRIMSON = (OBJECT_TYPE_NOTIFICATION_CLASS, 1)         # Notification Class 1
OBJECT_TYPE_EVENT_LOG = 25
OBJECT_TYPE_SCHEDULE = 17
OBJECT_TYPE_CALENDAR = 6
BEIGE = (OBJECT_TYPE_EVENT_LOG, 1)                    # Event Log 1
SAFFRON = (OBJECT_TYPE_SCHEDULE, 1)                   # Schedule 1, writes Chartreuse at priority 8
CREAM = (OBJECT_TYPE_CALENDAR, 1)                     # Calendar 1, Date_List = December 25
CHARTREUSE = (wiretest.OBJECT_TYPE_ANALOG_OUTPUT, 1)  # Analog Output 1, Saffron's target
PROPERTY_LOG_BUFFER = 131
PROPERTY_ENABLE = 133
PROPERTY_RECORD_COUNT = 141
PROPERTY_TOTAL_RECORD_COUNT = 145
SCHEDULE_WRITE_PRIORITY = 8
SCHEDULE_DEFAULT_VALUE = 20.0
SCHEDULE_WEEKLY_VALUE = 75.0          # Monday 08:00 onwards
SCHEDULE_EXCEPTION_VALUE = 5.0        # every date in Cream's Date_List
WORKSTATION_DEVICE_INSTANCE = 389108                  # Crimson's recipient (device form)
RECIPIENT_PROCESS_IDENTIFIER = 1                      # ... and its process id
NOTIFICATION_CLASS = 1
PRIORITY_TO_OFFNORMAL = 100
PRIORITY_TO_FAULT = 50
PRIORITY_TO_NORMAL = 200
PROPERTY_NUMBER_OF_APDU_RETRIES = 73
OPERATOR_PROCESS_IDENTIFIER = 7                      # the workstation's own process (LSO / ack)
NOTIFICATION_WAIT = 5.0                               # seconds allowed for a notification to arrive
QUIET_WAIT = 2.0                                      # seconds watched to show that nothing arrives
SIMULATION_CONTROL_VARIABLE = "BALSC_SIMULATION_CONTROL_PORT"
ERROR_CLASS_OBJECT = 1
ERROR_CODE_UNKNOWN_OBJECT = 31
REQUEST_ATTEMPTS = 3                                  # a plain client's tries per request (see client())
REQUEST_TIMEOUT = 0.5                                 # seconds; a loopback answer takes milliseconds


def parser(description):
    arguments = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    arguments.add_argument("--exe", default=str(wiretest.default_exe(REPOSITORY, "BACnetExampleBALSC")),
                           help="path to BACnetExampleBALSC (default: build/BACnetExampleBALSC)")
    arguments.add_argument("--port", type=int, default=47836,
                           help="the controller's UDP port (default 47836); the test control channel uses port + 1")
    return arguments


def workstation():
    """The operator workstation (a wiretest.Workstation): a request that gets NO answer at all is
    sent again once, with a visible [RETRY] line - a lost UDP datagram, seen about 3 in 1000 on a
    busy Windows host. An Error or Reject is an answer and is never retried."""
    return Workstation(retries=1)



def client():
    """A wiretest.Client whose unanswered requests are sent again after REQUEST_TIMEOUT, with a
    visible [RETRY] line, up to REQUEST_ATTEMPTS times - as a BACnet client does."""
    return wiretest.Client(retries=REQUEST_ATTEMPTS - 1, timeout=REQUEST_TIMEOUT)


def write(client, port, object_reference, property_identifier, value_octets, priority=None):
    return client.write_property(port, *object_reference, property_identifier, value_octets, priority)


def refused(answer):
    """Was the request answered with an Error or a Reject?"""
    return answer.answered and answer.frame.pdu_type in (wiretest.PDU_ERROR, wiretest.PDU_REJECT)


def describe(answer):
    return answer.describe()


def start_controller(args):
    """The example, with its SIMULATION test control channel on --port + 1."""
    return wiretest.start(args.exe, ["--port", args.port], "controller",
                          environment={SIMULATION_CONTROL_VARIABLE: args.port + 1})


def detector(args, reading):
    """Move the simulated detector: 'quiet', 'smoke' or 'fault'. Returns the channel's reply."""
    with wiretest.SimulationControl(args.port + 1) as control:
        return control.ask(f"detector {reading}")


def write_recipient_list(workstation, args, destinations):
    """WriteProperty of Crimson's Recipient_List (a concatenation of alarm_codec.destination())."""
    return workstation.request(lambda invoke_id: wiretest.write_property_request(
        invoke_id, *CRIMSON, alarm_codec.PROPERTY_RECIPIENT_LIST, destinations), args.port)


def write_enable(workstation, args, enable):
    """WriteProperty of Event Log 1's Enable."""
    return workstation.request(lambda invoke_id: wiretest.write_property_request(
        invoke_id, *BEIGE, PROPERTY_ENABLE, wiretest.application_boolean(enable)), args.port)


def read_event_log(workstation, args, reference_index=None, count=None):
    """(ReadRange-ACK dict or None, its records, the Answer) for Event Log 1's Log_Buffer."""
    answer = workstation.request(lambda invoke_id: wiretest.services.read_range_request(
        invoke_id, *BEIGE, PROPERTY_LOG_BUFFER, reference_index, count), args.port)
    log = wiretest.services.parse_read_range_ack(answer)
    return log, (wiretest.services.event_log_records(log["item_data"]) if log else []), answer


def is_bound(workstation, args):
    """Does the panel's Device_Address_Binding list Device 389108 (the workstation)?"""
    answer = workstation.request(lambda invoke_id: wiretest.read_property_request(
        invoke_id, *DEVICE, wiretest.PROPERTY_DEVICE_ADDRESS_BINDING), args.port)
    return answer.ok and (wiretest.OBJECT_TYPE_DEVICE, WORKSTATION_DEVICE_INSTANCE) in         wiretest.decoded_values(answer.value_octets)


def announce(workstation, args, seconds=5.0):
    """The workstation's I-Am as Device 389108 - what lets the panel address its alarms - sent
    (again each second) until the panel's Device_Address_Binding shows it. Returns whether it does."""
    def announced_and_bound():
        workstation.announce(WORKSTATION_DEVICE_INSTANCE, args.port)
        return wiretest.wait_until(lambda: is_bound(workstation, args), 1.0)
    return bool(wiretest.wait_until(announced_and_bound, seconds, interval=0))


def read(workstation, args, object_reference, property_identifier, array_index=None):
    """The decoded value of one property, or None (the Answer is printed on failure)."""
    answer = workstation.request(lambda invoke_id: wiretest.read_property_request(
        invoke_id, *object_reference, property_identifier, array_index), args.port)
    if not answer.ok:
        print(f"      read {object_reference} property {property_identifier}: {answer.describe()}")
    return answer.value


def life_safety_operation(workstation, args, operation, object_reference=None, source="Operator Olive"):
    return workstation.request(lambda invoke_id: wiretest.services.life_safety_operation_request(
        invoke_id, OPERATOR_PROCESS_IDENTIFIER, source, operation, object_reference), args.port)


def get_event_information(workstation, args):
    """(summaries, more_events, Answer) from one GetEventInformation."""
    answer = workstation.request(lambda invoke_id: alarm_codec.get_event_information_request(invoke_id), args.port)
    if answer.frame is None or answer.frame.pdu_type != wiretest.PDU_COMPLEX_ACK:
        return None, None, answer
    summaries, more_events = alarm_codec.parse_event_summaries(answer.frame.payload)
    return summaries, more_events, answer


def summary_for(summaries, object_reference):
    for entry in summaries or []:
        if entry["object"] == object_reference:
            return entry
    return None


def describe_summary(entry):
    if entry is None:
        return "not listed"
    return f"{entry['object']} event-state={entry.get('event_state')} acked={entry.get('acked_transitions')}"


def acknowledge(workstation, args, object_reference, event_state, time_stamp, source="Operator Olive"):
    """AcknowledgeAlarm, the time of acknowledgment being now (host clock)."""
    now = time.localtime()
    time_of_acknowledgment = (bytes([now.tm_year - 1900, now.tm_mon, now.tm_mday, now.tm_wday + 1]),
                              bytes([now.tm_hour, now.tm_min, now.tm_sec, 0]))
    return workstation.request(lambda invoke_id: alarm_codec.acknowledge_alarm_request(
        invoke_id, OPERATOR_PROCESS_IDENTIFIER, *object_reference, event_state, time_stamp, source,
        time_of_acknowledgment), args.port)


def notification_from(object_reference, notify_type, to_state=None):
    def matches(notification):
        return (notification.event_object == object_reference and notification.notify_type == notify_type and
                (to_state is None or notification.to_state == to_state))
    return matches


def waited(notification, seconds=None):
    return notification.describe() if notification else f"nothing in {seconds or NOTIFICATION_WAIT} s"


__all__ = ["Workstation", "alarm_codec", "wiretest"]
