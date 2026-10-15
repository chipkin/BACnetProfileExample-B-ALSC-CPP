# TODO - B-ALSC features not yet implemented

This example implements as much of the B-ALSC (Advanced Life Safety Controller) profile as
the CAS BACnet Stack's customer-facing API supports. B-ALSC is B-LSC plus an Event Log and
internal scheduling; this example is seeded from `BACnetProfileExample-B-LSC-CPP`, and items
1-2 are the same as B-LSC's. The items below are what it does not do, why, and what it would
take. Re-check every entry whenever the Stack Pin moves. Checked at stack `6.x` @
`64b2cfac5` (6.0.23), 2026-10-15.

Two old items are gone:

- **Old item 0, "Life Safety Point/Zone objects cannot serve almost any property".** At
  `64b2cfac5` the stack falls through to this example's callbacks (stack #2187): the
  discovery Wire Test reads every property Amber and Azure list, and a WriteProperty of
  Amber's `Present_Value` = alarm / fault / quiet moves `Event_State` to life-safety-alarm /
  fault / normal with an event notification each time. Stack issue
  [#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036) (customer
  `AddLifeSafetyPointObject` / `AddLifeSafetyZoneObject` exports) is still open, for item 1
  and for the stack's own life-safety engine (Mode / Accepted_Modes / Silenced / zone
  roll-up), which this example still stands in for with its own state.
- **Old item 3, "Event Log 1 cannot demonstrate capturing Amber's/Azure's alarm".** It
  followed from old item 0. At `64b2cfac5`, with Beige's `Enable` written TRUE, Amber
  `Present_Value` 2 / 0 / 3 / 0 moved `Record_Count` 1 -> 3 -> 5 -> 7 -> 9. The records'
  content was not read back with ReadRange in that check.

## 1. Life Safety Zone 1 (Azure) Zone_Members cannot be set

`Zone_Members` (cl. 12.16, required, a `BACnetLIST of BACnetDeviceObjectReference`) is listed
and reads as an **empty list** at `64b2cfac5`: the stack serves it, but the only way to fill
it is `BACnetStackTestTool_SetLifeSafetyZoneMembers` in `CASBACnetStackTestToolDLL.h`, and
this series uses the customer interface only.

**Blocked on** [chipkin/cas-bacnet-stack#2036](https://github.com/chipkin/cas-bacnet-stack/issues/2036)
(open; owner-approved as a customer-interface addition under tracking issue #2159).

## 2. LifeSafetyOperation (service 37) is registered but not enabled

`main.cpp` registers `BACnetStack_RegisterCallbackLifeSafetyOperation` and implements
`LifeSafetyOperation()`. The stack's default preset (`STACK_OPTION_TARGET_FULL`) does not
compile the service (`STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION` is set only by
`BACNET_STACK_TESTTOOL`), so the example leaves the service bit off and prints the stack's
"This feature was not compiled" line at start-up.

**This is a real gap in the profile.** An earlier version of this file said DM-LSO-B is "not
itself a BIBB the B-ALSC profile requires". AE-LS-B, which B-ALSC does require, lists
LifeSafetyOperation under Execute (135-2024 K.2.13: "Life safety device B is able to generate
life safety notifications and is able to process silence and reset operations on its life
safety objects"). So AE-LS-B is met only in part.

**To do (phase 2):** turning the option on needs no stack edit. This example's own
`CMakeLists.txt` can add it to the adapter target, the way `BACnetProfileExample-B-LS-CPP`
adds `STACK_OPTION_WRITE_GROUP`:

```cmake
target_compile_definitions(cas_bacnet_stack_adapter PRIVATE STACK_OPTION_DM_LSO_LIFE_SAFETY_OPERATION)
```

(SOURCE build; a prebuilt STATIC/DLL library must be built with it.) Then enable
`SERVICE_LIFE_SAFETY_OPERATION` and prove silence/reset with a Wire Test.

## 3. Profile-functional gaps (phase 2)

- **Event Log 1 starts with `Enable` FALSE**, so it records nothing until a client enables it.
- **Only a client write raises an alarm**; there is no simulated detector.
- **No particular recipient.** Notification Class 1 "Crimson" sends to the local subnet
  broadcast, unconfirmed. "Adjustment of alarm / event parameters including notification
  distribution" (L.5.1) has not been shown (whether Crimson's Recipient_List is writable has
  not been checked).
- **AcknowledgeAlarm and GetEventInformation** are enabled but have not been exercised end to
  end at this pin.
- **Calendar 1 "Cream"** is added with plain `BACnetStack_AddObject`, so its `Date_List` is
  empty and `Present_Value` is `false`. Stack #963 and #2034 are closed:
  `BACnetStack_AddCalendarObject` now holds a Date_List in the stack. Not adopted yet.
- **The Schedule is driven by a key (`s`)** for the demo; a Wire Test needs a headless
  trigger.
- **No Wire Test of the Profile Function yet.** `tests/` has the discovery test only.
