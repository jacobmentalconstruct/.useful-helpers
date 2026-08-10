# Superseded assertions

Assertions **removed from the active cumulative proof set** because an
operator-approved architectural correction retired their premise.

Mechanism: `.bcc/TRANCHE_PROTOCOL.md` §5.1.

## How this differs from `_deferred/`

They are not the same thing, and conflating them would lose the distinction that
makes supersession honest.

| | `_deferred/` | `_superseded/` |
| --- | --- | --- |
| The tranche | declared, **never implemented**, withdrawn | implemented, **parked**, proven |
| The assertion | never entered the active suite | was active and is now removed |
| Why | scope changed before work began | its premise was retired after it was proven |
| Expected future | salvaged into a redeclared tranche | replaced by a different invariant, or nothing |

## The rule these files exist to serve

> Parked tranche history is immutable; active cumulative proof describes the current
> architecture and may be surgically replaced only by an explicitly operator-approved
> superseding tranche, with provenance.

The journal is **historical evidence** — never rewritten. The gate suite is
**current proof** — replaceable. A retired assertion is preserved here verbatim so
that removing it from the suite is not the same as deleting it from project memory.

Every file here records: origin, when it was proven, what supersedes it, the
operator authority, the historical record's location, why it was retired, and the
replacement invariant or the tranche that owes one.
