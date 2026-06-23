# Plan (STUB): B-ALSC (Advanced Life Safety Controller) — C++ example

> **STATUS: STUB.** Seed facts below. Expand from
> [`bacnet-profile-plan-template.md`](../../bacnet-profile-plan-template.md) after the
> sample plans ([B-LD](../../BACnetProfileExample-B-LD-CPP/docs/plan.md),
> [B-BC](../../BACnetProfileExample-B-BC-CPP/docs/plan.md)) are reviewed.

**Profile:** B-ALSC · **Family:** Annex L.5 (Life Safety Controller) · **Role:** B ·
**Archetype:** Controller · **Difficulty:** 4/5 · **Build wave:** 3 (builds on B-LSC)

**Thesis:** B-LSC **plus** an **Event Log** and internal scheduling. The delta over
B-LSC is small — that is the point: a customer diffs B-ALSC against B-LSC.

## Required BIBBs (profiles.md L.5)
B-LSC's set **+ AE-EL-I-B, SCHED-I-B**.

## Services to enable
- All of B-LSC's services + Event Log support + Schedule (read-only — see gap).

## Objects (baseline + B-LSC objects + )
- Event Log 1, Schedule 1 + Calendar 1 (read-only).

## Shared features
- **DEFINE:** F-EVENTLOG (Event Log object — first AE-EL-I-B).
- **REUSE:** everything from B-LSC + F-SCHED (read-only — gap).

## Known stack gaps
- **SCHED-I-B needs the Schedule execution engine** (standard DLL lacks it) →
  read-only Schedule object + `TODO.md` (master plan §7 risk 1; B-AAC TODO §1).
- Recipient-by-address (inherited from F-ALARM). profiles.md: ✅ S67.

## Notes / open questions
- Build **immediately after B-LSC** (it is B-LSC + two objects). F-EVENTLOG is its
  only genuinely new feature; get it canonical (B-ACC and B-AEC reuse it).
