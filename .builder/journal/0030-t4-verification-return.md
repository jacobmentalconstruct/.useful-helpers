# 0030 - T4 verification return

Date: 2026-08-27

Status transition: T4 Awareness AWAITING_APPROVAL -> VERIFYING.

## Operator review finding

The operator returned T4 for a bounded freshness and basis repair. The declared T4
sentence required awareness freshness to detect a target change or substrate-basis
mismatch. The submitted implementation and tests exercised target mutation after
awareness creation, but did not independently witness a target mutation after T3
refresh and before T4 awareness refresh.

This is not a T4 redesign. The declaration and boundary-hardening amendment remain in
force. T4 must not be parked, P4 must not be credited, and T5 must not be declared.

## Required repair

The repair must establish a T3-owned API for a coherent awareness basis/current refresh
view, compose T4 awareness from that specific basis rather than accumulated substrate
history, bind awareness freshness to the T3-observed basis, prevent historical resource
or claim leakage after deletion/replacement transitions, add adversarial behavioral
fixtures, strengthen the T4 gate with a behavioral witness, and rerun focused T4,
canonical pytest/Ruff, T4, then cumulative T3/T2/T1/T0 from the repaired review
candidate before resubmitting AWAITING_APPROVAL.

## Next action

Repair only the bounded basis/freshness invariant and resubmit T4 for operator review.
