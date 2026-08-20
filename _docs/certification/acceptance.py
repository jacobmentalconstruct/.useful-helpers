#!/usr/bin/env python3
"""
FILE:       _docs/certification/acceptance.py
ROLE:       The acceptance-walk COVERAGE rule - closure gate, C4a.
DOMAIN:     factory
DOES:       Reads a set of harness run.json records and answers one question:
            was every required property actually MEASURED, on a target where the
            answer was knowable? Fails for COVERAGE, not only for per-run failures.
DEPENDS ON: stdlib only.
WIRES TO:   _harness/runs/*/run.json, produced by _harness/harness.py.
NOTES:      WHY THIS IS SEPARATE FROM certify.py. certify.py certifies ONE commit of the
            product: lint, suite, gates, and a single discovery pass. This certifies the
            ACCEPTANCE WALK - several runs across several targets - and the thing it adds
            is the one certify.py structurally cannot see from a single record: whether an
            axis was ever measured at all.

            THE FIVE STATES, AND NONE OF THEM COLLAPSES INTO PASS.

              PASS            measured, and it met the bar
              FAIL            measured, and it did not
              N/A             the property genuinely does not apply here
              NO-ORACLE       applicable and RELEVANT, but unmeasurable on this target
                              because nothing establishes the right answer
              NO-THRESHOLD    measured, but no acceptance bar has ever been declared

            The last two are the ones that get lost. NO-ORACLE is not N/A: truthfulness
            matters enormously on a real adopted target - we simply cannot compute a
            false-positive rate there without independently establishing what is true.
            Calling that "not applicable" claims the property is irrelevant when it is
            merely unmeasured. NO-THRESHOLD is not PASS: `tool_health` reports a rate
            nobody ever set a bar for, and a number without a bar is not a verdict.

            WHY REAL TARGETS AND CONTROLS BOTH. Synthetic targets alone risk a product
            exquisitely adapted to its own tests. Real targets alone risk beautiful green
            reports in places where correctness was never measurable. Real targets prove
            usefulness under uncertainty; controlled targets prove correctness where truth
            is knowable. Neither substitutes for the other, so this requires both.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PASS, FAIL = "PASS", "FAIL"
NOT_APPLICABLE = "N/A"
NO_ORACLE = "NO-ORACLE"
NO_THRESHOLD = "NO-THRESHOLD"

#: States that may NEVER satisfy a coverage requirement. Named as a set rather than
#: tested ad hoc, so that adding a sixth state cannot silently start counting as green.
NOT_EVIDENCE = (FAIL, NOT_APPLICABLE, NO_ORACLE, NO_THRESHOLD)


def _run_executed(score: dict) -> bool:
    """Did this run actually happen? Verdict axes pass AND tools were exercised.

    `tool_health.ran == 0` is the specific signal, not a proxy: it was 0 in every run of
    the nine days the discovery pass was silently dead, and non-zero in every good one.
    An exit code cannot tell those apart; this can.
    """
    verdicts = [v.get("pass") for v in score.values()
                if isinstance(v, dict) and "pass" in v]
    ran = (score.get("tool_health") or {}).get("ran") or 0
    return bool(verdicts) and all(verdicts) and ran > 0


def composition_state(record: dict) -> tuple[str, str]:
    """PASS / FAIL / NO-ORACLE / N/A for the composition axis of one run."""
    truth = record.get("ground_truth") or {}
    comp = (record.get("score") or {}).get("composition")
    has_oracle = (truth.get("expected_composite") is not None
                  or bool(truth.get("expected_subsystem_domains")))
    if not has_oracle:
        # Deliberately NOT N/A. A real adopted target may well be composite; we simply
        # have nothing that says what the right answer is.
        return NO_ORACLE, ("no composition oracle: the target declares neither "
                           "expected_composite nor expected_subsystem_domains")
    if comp is None:
        return FAIL, "an oracle is declared but `score.composition` was not produced"
    if comp.get("composite_expected") is None and not truth.get(
            "expected_subsystem_domains"):
        return NOT_APPLICABLE, "the oracle declares no composite expectation"
    problems = []
    if comp.get("composite_correct") is not True:
        problems.append(f"composite={comp.get('composite')!r} "
                        f"expected={comp.get('composite_expected')!r}")
    if comp.get("subsystems_correct") != comp.get("subsystems_expected"):
        problems.append(f"subsystems {comp.get('subsystems_correct')}"
                        f"/{comp.get('subsystems_expected')} placed")
    if comp.get("mismatches"):
        problems.append(f"mismatches={comp.get('mismatches')}")
    if problems:
        return FAIL, "; ".join(problems)
    return PASS, (f"composite correct, {comp.get('subsystems_correct')}"
                  f"/{comp.get('subsystems_expected')} subsystems placed")


def truthfulness_state(record: dict) -> tuple[str, str]:
    """PASS / FAIL / NO-ORACLE for the truthfulness axis of one run.

    THE DISCRIMINATING CLAUSE IS THE POINT. `false_positives == 0` on its own is also
    exactly what "nothing meaningful was exercised" looks like - a tool that finds
    nothing scores a perfect zero. Requiring naive > 0 AND policy_prevented > 0 forces
    the record to show that the machinery HAD SOMETHING TO DISTINGUISH and distinguished
    it: naive produced a false positive, policy prevented it, the faithful output carried
    none, and the genuine positive was still found.

    Same discipline as T8's stale-preview interference preserving the pattern's match
    count: make the easy explanation impossible.
    """
    truth = record.get("ground_truth") or {}
    t = (record.get("score") or {}).get("truthfulness") or {}
    if not truth.get("false_positive_bait"):
        return NO_ORACLE, "no truthfulness oracle: the target plants no false_positive_bait"
    fp, naive = t.get("false_positives"), t.get("naive_false_positives")
    prevented, missed = t.get("policy_prevented"), t.get("missed_true_positives")
    if any(v is None for v in (fp, naive, prevented, missed)):
        return FAIL, (f"bait is planted but the score is null: false_positives={fp!r} "
                      f"naive={naive!r} prevented={prevented!r} missed={missed!r}")
    problems = []
    if fp != 0:
        problems.append(f"faithful false_positives={fp}")
    if missed != 0:
        problems.append(f"missed_true_positives={missed}")
    if not (naive > 0 and prevented > 0):
        problems.append(
            f"the discriminating path is not demonstrated (naive={naive}, "
            f"prevented={prevented}) - zero false positives with nothing prevented is "
            "indistinguishable from an analysis that found nothing at all")
    if problems:
        return FAIL, "; ".join(problems)
    return PASS, (f"naive {naive} -> prevented {prevented} -> faithful {fp}, "
                  f"missed {missed}")


def tool_health_state(record: dict) -> tuple[str, str]:
    """Always NO-THRESHOLD until the harness declares a bar. Reported, never counted."""
    h = (record.get("score") or {}).get("tool_health") or {}
    return NO_THRESHOLD, (f"ran={h.get('ran')} ok={h.get('ok')} rate={h.get('rate')} - "
                          "the harness declares no acceptance bar for this rate, so it "
                          "is evidence without a verdict")


def evaluate(records: list[dict], real_targets: int = 3) -> dict:
    """The coverage rule. `records` are harness run.json dicts."""
    rows = []
    for rec in records:
        score = rec.get("score") or {}
        comp, comp_why = composition_state(rec)
        tru, tru_why = truthfulness_state(rec)
        th, th_why = tool_health_state(rec)
        rows.append({
            "target": rec.get("target"),
            "run_id": rec.get("run_id"),
            "executed": _run_executed(score),
            "oracle_bearing": bool((rec.get("ground_truth") or {})),
            "composition": {"state": comp, "why": comp_why},
            "truthfulness": {"state": tru, "why": tru_why},
            "tool_health": {"state": th, "why": th_why},
        })

    executed_real = [r for r in rows if r["executed"] and not r["oracle_bearing"]]
    comp_pass = [r for r in rows if r["composition"]["state"] == PASS and r["executed"]]
    tru_pass = [r for r in rows if r["truthfulness"]["state"] == PASS and r["executed"]]

    reqs = {
        "c4_real_targets_exercised": {
            "ok": len(executed_real) >= real_targets,
            "detail": f"{len(executed_real)} of {real_targets} real/adopted targets "
                      "executed successfully",
        },
        "composition_calibrated": {
            "ok": bool(comp_pass),
            "detail": (f"measured and correct on {[r['target'] for r in comp_pass]}"
                       if comp_pass else
                       "no run MEASURED composition on an oracle-bearing target. A null "
                       "axis cannot satisfy coverage"),
        },
        "truthfulness_calibrated": {
            "ok": bool(tru_pass),
            "detail": (f"measured and discriminating on {[r['target'] for r in tru_pass]}"
                       if tru_pass else
                       "no run MEASURED truthfulness with the naive -> prevented -> "
                       "faithful path demonstrated. A null axis cannot satisfy coverage"),
        },
    }
    return {"ok": all(v["ok"] for v in reqs.values()), "requirements": reqs, "runs": rows}


def load(paths: list[Path]) -> list[dict]:
    out = []
    for p in paths:
        rj = p / "run.json" if p.is_dir() else p
        if rj.is_file():
            out.append(json.loads(rj.read_text(encoding="utf-8")))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Acceptance-walk coverage (closure gate C4a)")
    ap.add_argument("runs", nargs="+", help="harness run directories or run.json files")
    ap.add_argument("--real-targets", type=int, default=3)
    ns = ap.parse_args(argv)
    result = evaluate(load([Path(p) for p in ns.runs]), ns.real_targets)
    for row in result["runs"]:
        print(f"{row['target']:28} executed={row['executed']}")
        for axis in ("composition", "truthfulness", "tool_health"):
            print(f"    {axis:14} {row[axis]['state']:13} {row[axis]['why']}")
    print()
    for name, req in result["requirements"].items():
        print(f"  [{'ok' if req['ok'] else 'FAIL'}] {name}: {req['detail']}")
    print(f"\nACCEPTANCE COVERAGE: {'PASS' if result['ok'] else 'FAIL'}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
