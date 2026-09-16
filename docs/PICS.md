# BACnet Protocol Implementation Conformance Statement (PICS)

For the **BACnet B-ALSC (Advanced Life Safety Controller) C++ example** -
see [README.md](../README.md).

> This is the PICS **for the example as shipped**. It describes a tutorial
> device announcing itself as a Chipkin demo, not a product. When you turn this
> example into your own device, this document is one of the things you rewrite:
> the vendor, model and version rows all come from the
> `CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of `main.cpp`. The
> example has **not** been submitted for BTL certification.

> **⚠ Life Safety Point 1 "Amber" and Life Safety Zone 1 "Azure" are
> configured but non-functional.** `BACnetStack_AddObject` (the only
> customer-facing way to create either object) never populates the stack's
> internal life-safety engine object, so almost every property on both
> objects answers `Error(...): object: unknown-object` over the wire -
> `Object_Identifier`/`Object_Type` are the only exceptions. This is a
> **stack-source gap**, not a defect in this example's code - see
> [chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036)
> and [TODO.md #0](../TODO.md). Both objects are marked accordingly in
> section 6 below. Event Log 1 "Beige" cannot demonstrate capturing either
> object's alarm for the identical reason (TODO.md #3), and Calendar 1
> "Cream"'s `Date_List` cannot be populated through the customer API
> ([cas-bacnet-stack#963](https://github.com/chipkin/cas-bacnet-stack/issues/963)).

## 1. Product description

| | |
|---|---|
| **Vendor Name** | Chipkin Automation Systems |
| **Vendor Identifier** | 389 |
| **Product Name** | CAS BACnet Stack Example - B-ALSC |
| **Product Model Number** | CAS BACnet Stack Example - B-ALSC |
| **Application Software Version** | 1.0.0 |
| **Firmware Revision** | 1.0.0 |
| **BACnet Protocol Version** | 1 |
| **BACnet Protocol Revision** | 24 |

**Product Description:** a tutorial BACnet/IP device built on the CAS BACnet
Stack that implements as much of the B-ALSC (Advanced Life Safety Controller)
profile as the stack's customer-facing API supports. It presents read-only
sensor objects, commandable outputs, a Life Safety Point and Zone with
intrinsic alarming (configured but currently non-functional over the wire -
see the callout above), an Event Log, and an internal Schedule + Calendar. It
is a tutorial for implementers of the B-ALSC profile.

## 2. BACnet standardized device profile (Annex L)

**B-ALSC - BACnet Advanced Life Safety Controller.**

This device claims exactly one profile. Because the B-ALSC requirements are a
superset of B-GENERAL's, a conformant B-ALSC device also satisfies
**B-GENERAL** (Annex L.8); that is subsumption, not a second claim.

## 3. BIBBs supported (Annex K)

| BIBB | Description | Supported |
|---|---|:---:|
| DS-RP-B | Data Sharing - ReadProperty - B | ✅ |
| DS-RPM-B | Data Sharing - ReadPropertyMultiple - B | ✅ |
| DS-WP-B | Data Sharing - WriteProperty - B | ✅ |
| DS-WPM-B | Data Sharing - WritePropertyMultiple - B | ✅ |
| DS-COV-B | Data Sharing - COV - B | ✅ |
| AE-LS-B | Alarm and Event - Life Safety - B | ✅ (generation is armed; the write path that triggers it is blocked by #2036 - see callout above) |
| AE-ACK-B | Alarm and Event - Acknowledge - B | ✅ |
| AE-INFO-B | Alarm and Event - Information - B | ✅ |
| AE-EL-I-B | Alarm and Event - Enrollment - Log - Initiate - B | ✅ (Event Log 1 "Beige"; own properties verified, alarm-capture demo blocked by #2036) |
| SCHED-I-B | Scheduling - Internal - B | ✅ (Schedule 1 "Saffron" + Calendar 1 "Cream") |
| DM-DDB-A | Device Management - Dynamic Device Binding - A | ✅ |
| DM-DDB-B | Device Management - Dynamic Device Binding - B | ✅ |
| DM-DOB-B | Device Management - Dynamic Object Binding - B | ✅ |
| DM-DCC-B | Device Management - Device Communication Control - B | ✅ |
| DM-TS-B | Device Management - Time Synchronization - B | ✅ |
| DM-UTC-B | Device Management - UTC Time Synchronization - B | ✅ |
| DM-RD-B | Device Management - Reinitialize Device - B | ✅ |

No other BIBBs are supported. `DM-LSO-B` (LifeSafetyOperation) is implemented
in `main.cpp` but not enabled on the wire (see TODO.md #2); it is not itself a
BIBB the B-ALSC profile requires.

## 4. Application services supported

| Service | Initiate | Execute |
|---|:---:|:---:|
| ReadProperty | no | **yes** |
| ReadPropertyMultiple | no | **yes** |
| WriteProperty | no | **yes** |
| WritePropertyMultiple | no | **yes** |
| SubscribeCOV | no | **yes** |
| Who-Is | no | **yes** |
| I-Am | **yes** | - |
| Who-Has | no | **yes** |
| I-Have | **yes** | - |
| ConfirmedEventNotification / UnconfirmedEventNotification | **yes** | - |
| AcknowledgeAlarm | no | **yes** |
| GetEventInformation | no | **yes** |
| ReadRange | no | **yes** (Event Log 1 "Beige" `Log_Buffer` only) |
| DeviceCommunicationControl | no | **yes** |
| ReinitializeDevice | no | **yes** |
| TimeSynchronization / UTCTimeSynchronization | no | **yes** |
| LifeSafetyOperation | no | no (implemented, not enabled - see TODO.md #2) |

An unsolicited I-Am is broadcast to the local subnet at start-up, as well as in
response to Who-Is.

## 5. Segmentation capability

Segmentation is **not supported** in either direction
(`Segmentation_Supported` = `no-segmentation`). `Max_APDU_Length_Accepted` is
1476 octets, the BACnet/IP maximum.

## 6. Standard object types supported

No object is dynamically creatable or deletable.

| Object type | Instance | Object_Name | Writable properties | Notes |
|---|:---:|---|---|---|
| Device | 389008 | Rainbow | - | Instance configurable at run time with `--deviceID`. |
| Analog Input | 1 | Bronze | - | `Present_Value` is COV-subscribable. |
| Binary Input | 1 | Emerald | - | - |
| Multi-State Input | 1 | Hot Pink | - | `State_Text` enabled. |
| Analog Output | 1 | Chartreuse | Present_Value | Commandable, 16-slot `Priority_Array`; also the Schedule write target. |
| Binary Output | 1 | Fuchsia | Present_Value | Commandable, 16-slot `Priority_Array`. |
| Multi-State Output | 1 | Indigo | Present_Value | Commandable, 16-slot `Priority_Array`. |
| Life Safety Point | 1 | Amber | Present_Value, Mode | ⚠ **Configured but non-functional** - only `Object_Identifier`/`Object_Type` are servable; every other property answers `unknown-object`. See [chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036) and TODO.md #0. |
| Life Safety Zone | 1 | Azure | Present_Value, Mode | ⚠ **Configured but non-functional**, same cause as Amber. `Zone_Members` additionally has no servable path at all (TODO.md #1). |
| Notification Class | 1 | Crimson | - | Routes Amber's/Azure's alarm notifications. |
| Event Log | 1 | Beige | Enable | Own properties (existence, `Log_Enable`, `ReadRange`, `Record_Count`) verified working; cannot demonstrate capturing Amber's/Azure's alarm (TODO.md #3, downstream of #2036). |
| Schedule | 1 | Saffron | - | Drives Chartreuse at priority 8 on a weekly + exception basis. |
| Calendar | 1 | Cream | - | `Date_List` cannot be populated through the customer API ([cas-bacnet-stack#963](https://github.com/chipkin/cas-bacnet-stack/issues/963)); `Present_Value` always answers `false`. |
| Network Port | 1 | Vermilion | - | Required on every device. |

The device instance is configurable at run time with `--deviceID` (BACnet
requires the device instance to be configurable).

## 7. Data link layer options

**BACnet/IP (Annex J)**, UDP port 47808 (0xBAC0) by default, configurable at run
time with `--port`.

BBMD is not supported, Foreign Device registration is not supported, and
BACnet/SC, MS/TP, Ethernet (Annex H) and PTP are not supported.

## 8. Device address binding

Static device binding is **not supported**. The device answers Who-Is/Who-Has
and does not initiate any confirmed request other than an EventNotification
(sent to the Notification Class's configured recipient list, not a bound
peer), so it never needs to bind one.

## 9. Networking options

None. The device is not a router, not a BBMD, and does not register as a
foreign device.

## 10. Character sets supported

UTF-8 (ANSI X3.4). Supporting a character set does not imply the device can
handle data in all character sets.

## 11. Objects and properties

<!-- OBJECTS-PROPERTIES:BEGIN (generated by tools/gen-objects-properties.py from docs/objects.json - do not edit here) -->
Every object this example creates, and every REQUIRED property of each (per ANSI/ASHRAE 135-2024 clause 12 and the stack's `docs/property-profile-reference.md`), plus the optional properties the example turns on. **Served by** says who answers a ReadProperty: the **stack** generates it, or the **app** serves it from a `GetProperty*` callback in `main.cpp`. A ⚠ row is a required property the app does not serve and the stack would fill with a default - that is a defect, not a feature.

### Device 389008 "Rainbow" - the device itself; the instance is configurable with --deviceID. The stack rows are device-wide facts only the stack knows - the protocol version and revision it implements, the services and object types it was configured with, the live object list and address-binding table. The accepted rows are the stack's configured defaults for APDU limits, segmentation, system status and database revision; an application that answered them from its own constants could contradict the stack, so this example does not

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| System_Status | BACnetDeviceStatus | stack default, accepted (Generic Enumerated default: `0`) | no |
| Vendor_Name | CharacterString | app | no |
| Vendor_Identifier | Unsigned16 | app | no |
| Model_Name | CharacterString | app | no |
| Firmware_Revision | CharacterString | app | no |
| Application_Software_Version | CharacterString | app | no |
| Description *(optional, enabled)* | CharacterString | app | no |
| Protocol_Version | Unsigned | stack | no |
| Protocol_Revision | Unsigned | stack | no |
| Protocol_Services_Supported | BACnetServicesSupported | stack | no |
| Protocol_Object_Types_Supported | BACnetObjectTypesSupported | stack | no |
| Object_List | BACnetARRAY[N] of BACnetObjectIdentifier | stack | no |
| Max_APDU_Length_Accepted | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_MAX_APDU_LENGTH_ACCEPTED`) | no |
| Segmentation_Supported | BACnetSegmentation | stack default, accepted (`BACnetSegmentation::noSegmentation`) | no |
| APDU_Timeout | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_APDU_TIMEOUT`) | no |
| Number_Of_APDU_Retries | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_NUMBER_OF_APDU_RETRIES`) | no |
| Device_Address_Binding | BACnetLIST of BACnetAddressBinding | stack | no |
| Database_Revision | Unsigned | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Analog Input 1 "Bronze" - REAL, degrees Celsius; starts at 21.5. Present_Value is DS-COV-B subscribable (BACnetStack_SetPropertySubscribable); the up/down key feeds subscribers via BACnetStack_UpdateValue

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Binary Input 1 "Emerald" - starts inactive

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Multi-state Input 1 "Hot Pink" - state 1 of 3: On, Off, Auto

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| State_Text *(optional, enabled)* | BACnetARRAY[N] of CharacterString | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Analog Output 1 "Chartreuse" - F-OUTPUTS (canonical: B-SA). commandable; 16-slot Priority_Array, Relinquish_Default 20.0 C, served by GetPropertyReal. Present_Value, Priority_Array and Current_Command_Priority are resolved by the stack from the priority array. ALSO the SCHED-I-B write target - Schedule 1 (Saffron) writes it at priority 8

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalReal | stack | no |
| Relinquish_Default | Real | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Binary Output 1 "Fuchsia" - F-OUTPUTS. commandable; 16-slot Priority_Array, Relinquish_Default inactive, served by GetPropertyEnumerated

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalBinaryPV | stack | no |
| Relinquish_Default | BACnetBinaryPV | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Multi-state Output 1 "Indigo" - F-OUTPUTS. commandable; 16-slot Priority_Array, Relinquish_Default state 1 of 3, served by GetPropertyUnsignedInteger

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | stack | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalUnsigned | stack | no |
| Relinquish_Default | Unsigned | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Life Safety Point 1 "Amber" - VERIFIED CRITICAL GAP (TODO.md #0, carried forward from BACnetProfileExample-B-LSC-CPP and re-verified against this repository's own build): almost every property on this object currently answers unknown-object over the wire, because BACnetStack_AddObject never populates the stack internal life-safety engine object (AddLifeSafetyPointObject/AddLifeSafetyZoneObject are not customer-exported) - see chipkin/cas-bacnet-stack#2036. F-LIFESAFETY / F-ALARM-LS (canonical: B-LSC). BACnetLifeSafetyState Present_Value: quiet(0)/alarm(2)/fault(3); Tracking_Value mirrors it (this example's simplification - see main.cpp file header for why it does not use the stack's internal, non-customer-exported life-safety engine). Present_Value is made WRITABLE beyond the profile's read-only column purely as this tutorial's alarm/fault trigger (mirrors B-AAC's Diamond) - and that WriteProperty is exactly what issue #2036 blocks. Mode is required-writable by the profile and accepted unconditionally (no customer-facing Accepted_Modes setter exists - see the file header); Accepted_Modes is therefore accepted at the stack's generic default. Event_State is NOT actually a stack default here - it is genuinely computed, because this example arms ChangeOfLifeSafety + fault intrinsic algorithms on Amber (SetIntrinsicChangeOfLifeSafetyAlgorithm/SetFaultLifeSafetyAlgorithm); it is marked accepted only because property-profile-reference.md's generic table does not know an algorithm was armed (same convention as B-AAC's Diamond). Present_Value is also DS-COV-B subscribable

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetLifeSafetyState | app | yes |
| Tracking_Value | BACnetLifeSafetyState | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Mode | BACnetLifeSafetyMode | app | yes |
| Accepted_Modes | BACnetLIST of BACnetLifeSafetyMode | stack default, accepted (Generic Enumerated default: `0`) | no |
| Silenced | BACnetSilencedState | app | no |
| Operation_Expected | BACnetLifeSafetyOperation | app | no |

### Life Safety Zone 1 "Azure" - VERIFIED CRITICAL GAP (TODO.md #0, carried forward from BACnetProfileExample-B-LSC-CPP and re-verified against this repository's own build): almost every property on this object currently answers unknown-object over the wire - see chipkin/cas-bacnet-stack#2036. F-LIFESAFETY / F-ALARM-LS. Event_State is genuinely computed (same as Amber's - ChangeOfLifeSafety + fault algorithms armed on Azure too), marked accepted for the same generator-limitation reason. Same shape as Amber (this example holds Azure's own independent Present_Value rather than rolling it up from Zone_Members - the stack's real zone roll-up engine is not customer-exported, see the file header). Zone_Members (cl. 12.16, required, BACnetLIST of BACnetDeviceObjectReference) has NO servable path on the customer surface: the only generic constructed-property callback, BACnetStack_RegisterCallbackGetPropertyConstructed, was moved to the test-tool DLL (CASBACnetStackDLL.h's own PR #193 review comment) and is forbidden by this series. See TODO.md and the filed stack issue - this is a real, verified gap, not a convenience shortcut

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetLifeSafetyState | app | yes |
| Tracking_Value | BACnetLifeSafetyState | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Mode | BACnetLifeSafetyMode | app | yes |
| Accepted_Modes | BACnetLIST of BACnetLifeSafetyMode | stack default, accepted (Generic Enumerated default: `0`) | no |
| Silenced | BACnetSilencedState | app | no |
| Operation_Expected | BACnetLifeSafetyOperation | app | no |
| Zone_Members | BACnetLIST of BACnetDeviceObjectReference | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Notification Class 1 "Crimson" - Priority, Ack_Required and Recipient_List are NOT stack DEFAULTS - they are genuinely populated, by BACnetStack_AddNotificationClassObject (Priority, Ack_Required) and BACnetStack_AddRecipientToNotificationClass (Recipient_List) at start-up. They are marked accepted only because property-profile-reference.md's generic per-type table does not know about this object-specific host-configuration API and so cannot credit them as stack-served. Routes Amber's and Azure's CHANGE_OF_LIFE_SAFETY / fault notifications

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Priority | BACnetARRAY[3] of Unsigned | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Ack_Required | BACnetEventTransitionBits | stack default, accepted (Generic BitString default: empty bitstring (zero bits - NOT ) | no |
| Recipient_List | BACnetLIST of BACnetDestination | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Event Log 1 "Beige" - F-EVENTLOG (canonical: this repository). Enable/Buffer_Size/Record_Count/Total_Record_Count/Log_Buffer/Status_Flags/Object_Identifier/Object_Type/Property_List are NOT stack defaults in the generic sense - they are genuinely held and served by the stack's own Event Log engine (BACnetStack_AddEventLogObject), answered from stack storage BEFORE this file's Get*/Set* callbacks are ever consulted; marked accepted only because property-profile-reference.md's generic table does not know about this object-specific engine. VERIFIED over the wire with a live bacpypes3 client against this repository's own build: Object_Name/Object_Type/Buffer_Size/Record_Count/Total_Record_Count read correctly; Enable (property id 133) round-trips a WriteProperty false->true correctly; ReadRange of Log_Buffer (service 35, RangeByPosition) succeeds and returns real BACnetLogRecords - toggling Enable was independently captured as a clause-12.27 log-status transition with no application code involved (Record_Count/Total_Record_Count moved 0->1, ReadRange returned exactly that record), proving the automatic capture hook is live in this build. NOT verified: capturing Amber's/Azure's own CHANGE_OF_LIFE_SAFETY notification - that requires Amber/Azure to actually reach alarm(2), which is blocked by the SAME root cause as the Life Safety Point/Zone gap above (issue #2036) - see TODO.md #3. BACnetStack_InsertEventLogRecord (the only app-facing way to seed a record directly) was moved to the test-tool surface in v6 and is forbidden by this series, so this example never calls it and never fakes a record. Event_State is accepted at the stack's generic default (normal) - this example does not arm intrinsic reporting on Beige itself (only on Amber/Azure), matching the doc comment on BACnetStack_AddEventLogObject: with neither an alarm engine nor a callback armed, the stack answers normal(0)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Enable | Boolean | stack default, accepted (Generic Boolean default: `false`) | yes |

### Schedule 1 "Saffron" - SCHED-I-B (identical pattern to B-AAC's canonical Saffron - this series' copy source for F-SCHED-I). Present_Value, Effective_Period, Schedule_Default, List_Of_Object_Property_References, Priority_For_Writing and Status_Flags are NOT stack DEFAULTS - they are genuinely held and served by the stack's Schedule engine (BACnetStack_AddScheduleObject plus the BACnetStack_SetSchedule*/AddSchedule* configuration calls in main.cpp); it writes Analog Output 1 (Chartreuse) Present_Value at priority 8. Present_Value, Effective_Period and Priority_For_Writing are marked accepted only because property-profile-reference.md's generic table does not know about the Schedule engine's own host-configuration API. One weekly transition (Monday 08:00) and one calendar-date exception (2026-12-25, via the inline calendar-entry form) are seeded at start-up; the 's' key (common/ 2.1.0's DemoAdvance) adds a transition for right now so the change can be observed without waiting for the wall clock. VERIFIED over the wire: Object_Name, Priority_For_Writing (8) and Schedule_Default all read back correctly

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Any | stack default, accepted (Stack-generated if commandable (resolves the priority array)) | no |
| Effective_Period | BACnetDateRange | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Schedule_Default | Any | stack | no |
| List_Of_Object_Property_References | BACnetLIST of BACnetDeviceObjectPropertyReference | stack | no |
| Priority_For_Writing | Unsigned(1..16) | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | app | no |
| Out_Of_Service | Boolean | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Calendar 1 "Cream" - exists for SCHED-I-B completeness alongside Saffron's exception, but its Date_List cannot be populated through the customer API (cas-bacnet-stack issue #963 - no read path for a Calendar object's Date_List; the only generic constructed-property callback is test-tool-only). Present_Value therefore always answers false rather than evaluating a Date_List that is never populated - see TODO.md. VERIFIED over the wire: Object_Name and Present_Value (false) both read back correctly

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Boolean | app | no |
| Date_List | BACnetLIST of BACnetCalendarEntry | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Network Port 1 "Vermilion" - BACnet/IP; Network_Type and Protocol_Level are set from BACnetStack_AddNetworkPortObject()'s arguments (IPv4, BACnet Application) at start-up, not a GetProperty callback like the object's other app-served rows; Changes_Pending is likewise computed and answered natively by the stack's Network Port object. Reliability has no fault condition this example detects, so it is accepted at the generic default (normal)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Network_Type | BACnetNetworkType | app | no |
| Protocol_Level | BACnetProtocolLevel | app | no |
| Changes_Pending | Boolean | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

<!-- OBJECTS-PROPERTIES:END -->

## 12. References

- ANSI/ASHRAE Standard 135-2024, Annex A (PICS template), Annex K (BIBBs),
  Annex L (device profiles), Clause 12 (object types), Clause 13 (alarm and
  event services).
- [README.md](../README.md) - what this example is and how to build it.
- [TUTORIAL.md](../TUTORIAL.md) - how to extend it, and how to keep this
  document honest when you do.
- [TODO.md](../TODO.md) - what is not implemented and why.
