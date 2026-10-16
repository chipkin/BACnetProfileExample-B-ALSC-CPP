# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""Generic Wire Test helpers that wiretest/ 0.6.0 does not have yet (proposed for 0.7.0).

Nothing here names B-LSC: each piece is a BACnet encoding or a harness tool any example
could use. Kept apart from the profile's tests so it can be folded into wiretest/ as is.

    life_safety_operation_request   LifeSafetyOperation-Request (cl. 21, cl. 13.13)
    announce                        send an I-Am for a Workstation, unicast, so a device that
                                    names it by DEVICE instance (a Recipient_List entry) can
                                    bind its address without hearing a broadcast
    SimulationControl               the client side of an example's loopback-only test control
                                    channel (one plain-text command per datagram, one reply)
    request_with_retry              Workstation.request() with wiretest.Client's opt-in, visible
                                    [RETRY] when nothing at all comes back
    read_range_request, parse_read_range_ack, event_log_records, application_signed
                                    ReadRange (cl. 15.8) and BACnetEventLogRecord decoding -
                                    copied verbatim from B-AEC-CPP's tests/aec_services.py
                                    (same 0.7.0 proposal), so the fold has one copy to take
"""
import socket
import struct

import wiretest
from wiretest import codec
from wiretest.codec import closing, confirmed_request, context_object_id, context_unsigned, opening, read_tag

# BACnetConfirmedServiceChoice life-safety-operation (cl. 21).
SERVICE_LIFE_SAFETY_OPERATION = 27

# BACnetLifeSafetyOperation (cl. 21).
LIFE_SAFETY_OPERATION_NONE = 0
LIFE_SAFETY_OPERATION_SILENCE = 1
LIFE_SAFETY_OPERATION_SILENCE_AUDIBLE = 2
LIFE_SAFETY_OPERATION_SILENCE_VISUAL = 3
LIFE_SAFETY_OPERATION_RESET = 4
LIFE_SAFETY_OPERATION_RESET_ALARM = 5
LIFE_SAFETY_OPERATION_RESET_FAULT = 6
LIFE_SAFETY_OPERATION_UNSILENCE = 7

# BACnetLifeSafetyState (cl. 21), the values the examples use.
LIFE_SAFETY_STATE_QUIET = 0
LIFE_SAFETY_STATE_ALARM = 2
LIFE_SAFETY_STATE_FAULT = 3

# BACnetSilencedState (cl. 21).
SILENCED_UNSILENCED = 0
SILENCED_AUDIBLE = 1
SILENCED_VISIBLE = 2
SILENCED_ALL = 3

# BACnetEventState / BACnetEventType values wiretest.alarm does not name yet.
EVENT_STATE_LIFE_SAFETY_ALARM = 5
EVENT_TYPE_CHANGE_OF_LIFE_SAFETY = 8

# BACnetReliability multi-state-fault (cl. 21) - the FAULT_LIFE_SAFETY algorithm's fault.
RELIABILITY_MULTI_STATE_FAULT = 9

# Error code invalid-operation-in-this-state (cl. 21 BACnetErrorCode).
ERROR_CODE_INVALID_OPERATION_IN_THIS_STATE = 139

# Life-safety property identifiers (cl. 21 BACnetPropertyIdentifier).
PROPERTY_MODE = 160
PROPERTY_OPERATION_EXPECTED = 161
PROPERTY_SILENCED = 163
PROPERTY_TRACKING_VALUE = 164
PROPERTY_ZONE_MEMBERS = 165


def life_safety_operation_request(invoke_id, process_identifier, source, operation, object_reference=None):
    """LifeSafetyOperation-Request (cl. 21): requestingProcessIdentifier [0], requestingSource [1],
    request [2], objectIdentifier [3] OPTIONAL. `object_reference` is (type, instance) or None
    ("all applicable objects", cl. 13.13.1.1.4)."""
    parameters = (codec.context_unsigned(0, process_identifier) + codec.context_character_string(1, source) +
                  codec.context_enumerated(2, operation))
    if object_reference is not None:
        parameters += codec.context_object_id(3, *object_reference)
    return codec.confirmed_request(invoke_id, SERVICE_LIFE_SAFETY_OPERATION, parameters)


def request_with_retry(workstation, build_apdu, port, retries=1, timeout=3.0):
    """workstation.request(), sent again (with a visible [RETRY] line) when NO answer comes back at
    all - a lost UDP datagram, seen about 3 in 1000 on a busy Windows host. An Error or Reject is an
    answer and is never retried. A request whose answer (not the request) was lost is executed
    twice; the second answer then shows that, so a test does not hide it."""
    answer = workstation.request(build_apdu, port, timeout=timeout)
    for attempt in range(retries):
        if answer.answered:
            break
        print(f"      [RETRY] no answer in {timeout} s - sending the request again (attempt {attempt + 2})", flush=True)
        answer = workstation.request(build_apdu, port, timeout=timeout)
    return answer


def announce(workstation, device_instance, port, ip="127.0.0.1", vendor_identifier=389):
    """Send an I-Am for `device_instance` from `workstation`'s socket to one device. A device
    whose Recipient_List names `device_instance` learns the workstation's address from it - the
    way a workstation's start-up I-Am reaches a panel, without relying on broadcasts (which do
    not reach a 127.0.0.1 socket)."""
    workstation.send_unconfirmed(codec.i_am(device_instance, vendor_identifier), port, ip)


class SimulationControl:
    """Client of an example's SIMULATION test control channel (loopback UDP, one plain-text
    command per datagram, one reply), e.g. B-GW-CPP's and B-LSC-CPP's simulation/SimulationControl."""

    def __init__(self, port, ip="127.0.0.1", timeout=2.0, retries=2):
        self.address = (ip, port)
        self.timeout = timeout
        self.retries = retries

    def command(self, text):
        """The reply text, or None if the example never answered (each lost datagram retried once
        more, visibly, up to `retries` times)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        try:
            for attempt in range(self.retries + 1):
                if attempt:
                    print(f"      [RETRY] simulation control '{text}' (attempt {attempt + 1})", flush=True)
                sock.sendto(text.encode("ascii"), self.address)
                try:
                    reply, _ = sock.recvfrom(256)
                    return reply.decode("ascii", "replace")
                except (socket.timeout, ConnectionResetError):
                    continue
            return None
        finally:
            sock.close()


# ---------------------------------------------------------------------------
# From B-AEC-CPP tests/aec_services.py (verbatim)
# ---------------------------------------------------------------------------

SERVICE_READ_RANGE = 26


def _signed_octets(value):
    for length in (1, 2, 3, 4):
        if -(1 << (8 * length - 1)) <= value < (1 << (8 * length - 1)):
            return value.to_bytes(length, "big", signed=True)
    raise ValueError(value)


def application_signed(value):
    """An application-tagged INTEGER (cl. 20.2.5), shortest two's-complement form."""
    body = _signed_octets(value)
    return bytes([0x30 | len(body)]) + body


def application_octet_string(octets):
    """An application-tagged OCTET STRING (cl. 20.2.8)."""
    if len(octets) < 5:
        return bytes([0x60 | len(octets)]) + octets
    if len(octets) < 254:
        return bytes([0x65, len(octets)]) + octets
    return bytes([0x65, 254]) + struct.pack(">H", len(octets)) + octets


def _context_signed(tag, value):
    body = _signed_octets(value)
    return bytes([(tag << 4) | 0x08 | len(body)]) + body


# ---------------------------------------------------------------------------
# ReadRange (cl. 15.8)
# ---------------------------------------------------------------------------

def read_range_request(invoke_id, object_type, instance, property_identifier, reference_index=None, count=None):
    """ReadRange-Request; with reference_index and count, the by-position range [3];
    without, no range (the whole list)."""
    parameters = context_object_id(0, object_type, instance) + context_unsigned(1, property_identifier)
    if reference_index is not None:
        parameters += (opening(3) + codec.application_unsigned(reference_index) +
                       application_signed(count) + closing(3))
    return confirmed_request(invoke_id, SERVICE_READ_RANGE, parameters)


def parse_read_range_ack(answer):
    """A ReadRange-ACK as {result_flags, item_count, item_data (the octets inside [5])}, or None."""
    if answer.frame is None or answer.frame.pdu_type != wiretest.PDU_COMPLEX_ACK:
        return None
    apdu = answer.frame.payload
    result = {"result_flags": None, "item_count": None, "item_data": b""}
    position = 3
    try:
        while position < len(apdu):
            number, is_context, kind, body, after = read_tag(apdu, position)
            if is_context and kind == "value" and number == 3:
                result["result_flags"] = codec.decode_application(bytes([0x80 | len(body)]) + body)
            elif is_context and kind == "value" and number == 4:
                result["item_count"] = int.from_bytes(body, "big")
            elif is_context and kind == "open" and number == 5:
                start = after
                depth = 1
                tag_start = after
                while depth:
                    tag_start = after
                    number, is_context, kind, _, after = read_tag(apdu, after)
                    depth += {"open": 1, "close": -1}.get(kind, 0)
                result["item_data"] = apdu[start:tag_start]
            position = after
    except (IndexError, struct.error):
        return None
    return result


def _constructed_end(octets, position):
    """Position just after the closing tag matching an opening tag already read."""
    depth = 1
    while depth:
        _, _, kind, _, position = read_tag(octets, position)
        depth += {"open": 1, "close": -1}.get(kind, 0)
    return position


def _notification_fields(octets):
    """The top-level context-tagged primitives of a ConfirmedEventNotification-Request's
    parameters (cl. 21.2), as {tag number: value bytes}; constructed ones are skipped."""
    fields = {}
    position = 0
    while position < len(octets):
        number, is_context, kind, body, position = read_tag(octets, position)
        if kind == "open":
            position = _constructed_end(octets, position)
        elif is_context and kind == "value":
            fields[number] = body
    return fields


def event_log_records(item_data):
    """BACnetEventLogRecords (cl. 21.6) from a ReadRange-ACK's item data, each as a dict:
    kind 'status' / 'notification' / 'time-change', and for a notification its
    process_identifier, initiating_device, event_object, from_state, to_state and the
    raw notification octets."""
    records = []
    position = 0
    while position < len(item_data):
        number, is_context, kind, _, position = read_tag(item_data, position)    # [0] timestamp open
        if not (is_context and number == 0 and kind == "open"):
            break
        timestamp_start = position
        position = _constructed_end(item_data, position)
        record = {"timestamp": item_data[timestamp_start:position]}
        number, is_context, kind, _, position = read_tag(item_data, position)    # [1] log-datum open
        number, is_context, kind, body, inner = read_tag(item_data, position)    # the CHOICE
        if number == 0 and kind == "value":                                     # log-status [0] BIT STRING
            record["kind"] = "status"
            record["log_status"] = body
            position = inner
        elif number == 1 and kind == "open":                                    # notification [1] SEQUENCE
            record["kind"] = "notification"
            end = _constructed_end(item_data, inner)
            notification = item_data[inner:end]
            fields = _notification_fields(notification)

            def identifier(tag):
                if tag not in fields:
                    return None
                raw = struct.unpack(">I", fields[tag])[0]
                return raw >> 22, raw & codec.MAX_INSTANCE
            record["notification"] = notification
            record["process_identifier"] = int.from_bytes(fields.get(0, b"\x00"), "big")
            record["initiating_device"] = identifier(1)
            record["event_object"] = identifier(2)
            record["from_state"] = int.from_bytes(fields[10], "big") if 10 in fields else None
            record["to_state"] = int.from_bytes(fields[11], "big") if 11 in fields else None
            position = end
        else:
            record["kind"] = "time-change"
            position = inner
        position = read_tag(item_data, position)[4]                             # [1] log-datum close
        records.append(record)
    return records
