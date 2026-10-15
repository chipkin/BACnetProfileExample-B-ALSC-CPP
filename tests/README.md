# B-ALSC Wire Tests

Tests that drive the running advanced life safety controller over BACnet/IP from outside it. For now
there is one: discovery, the way a client such as Chipkin BACnet Explorer finds a
device and reads everything it says it has. It does not test the B-ALSC
Profile Function. That needs a Python peer as the
notification recipient, alarm/acknowledge, Event Log and Schedule tests, and a
LifeSafetyOperation test: phase-2 work (see TODO.md).

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
47821) is the UDP port the test starts the example on. It takes a few seconds.
CI (`.github/workflows/release.yml`) runs it on Linux after the smoke test.

## The setup

```
test client (127.0.0.1, ephemeral UDP port)  - the Peer
    |  BACnet/IP, unicast
BACnetExampleBALSC  UDP --port               - Device 389008
```

The Peer is a Python BACnet client (`wiretest.Client`), never another example's
binary. It plays a BACnet client such as Chipkin BACnet Explorer.

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
   and fails the check. 135-2024 cl. 12.1.1.4.1: Property_List holds "one
   property identifier for each property that exists within the object".
4. Network Port 1's **`IP_DNS_Server` (406)**, **`FD_BBMD_Address` (418)** and
   **`FD_Subscription_Lifetime` (419)** are each listed and read as a value: the
   three reads Explorer 4.23.2.0 found failing at stack 6.0.21 (reported against
   B-SS-CPP as #20, #21, #22; every example in the series serves the same
   Network Port).
5. Event Log 1's **`Log_Buffer` (131)** is the one listed property ReadProperty
   must refuse: "The log buffer is not network accessible except through the use
   of the ReadRange service" (135-2024 cl. 12.27.13), and a property "not
   accessible using this service" answers PROPERTY / READ_ACCESS_DENIED (cl.
   15.5.1.3.1). It is left out of step 3 and checked for exactly that error.

## Results

Run 2026-10-15, stack `6.x` @ `64b2cfac5` (6.0.23), example v1.1.0:

| Platform | Build | Result |
|---|---|---|
| Windows 11 | STATIC (stack `ReleaseLib` `x64`, VS 18, NMake) | 21/21 - PASS x3, 214 reads |
| Linux (WSL Ubuntu 22.04) | SOURCE (g++) | 21/21 - PASS x3, 214 reads |

Before this update's fixes the same run failed 19/20 (the Log_Buffer check did
not exist yet) on four reads:

```
[UNREADABLE] Device 389008 property 56: Error class=2 code=72
[UNREADABLE] Device 389008 property 57: Error class=2 code=72
[UNREADABLE] Schedule 1 property 85: Error class=2 code=72
[UNREADABLE] Event Log 1 property 131: Error class=2 code=27
```

Local_Date (56) and Local_Time (57) were listed but not served (the example
executes TimeSynchronization, so 135-2024 Table 12-13 footnotes 3 and 4 put them
there); serving them also fixed Schedule 1's Present_Value (85), which the stack's
Schedule engine computes from Local_Date. Log_Buffer (131) was a correct refusal:
the test now expects exactly that error for it (step 5 below).
