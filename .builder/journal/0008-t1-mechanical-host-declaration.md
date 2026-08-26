# T1 Mechanical Hands + Governed Host Declaration

- Date: 2026-08-26
- Tranche: T1 Mechanical Hands + Governed Host
- Entry class: declaration and scope-review submission
- Transition: PROVISIONAL -> DECLARED / AWAITING DECLARATION APPROVAL
- Preconditions: T0 alignment PARKED in entry `0007`
- Measured source: `38892a5` (`Park operator-approved T0 vision alignment`)
- Product implementation authorized: no

## Declared outcome

Five manifest-defined mechanical operations execute against a small product-neutral
transported context with no Sidecar installation identity dependency, while the Sidecar
CLI host still validates a complete instance and refuses unauthorized, invalid, or
uncontained calls before child execution.

This tranche establishes the seam between portable capability and Sidecar-hosted
governed use. It does not merely prove that the five provisional tools can already run.

## Measured mechanical requirements

The matrix below comes from each manifest's declared domains/path arguments and an AST
inventory of `context.*` members used by each tool body.

| Tool | Manifest access | Mechanical inputs/context actually used | Does not intrinsically need |
|---|---|---|---|
| `hash_file` | observe; reads target; host-resolved `path` | sanctioned resolved file path; target root only to emit canonical relative handle | instance root, UUID, state, registry, governance |
| `read_file` | observe; reads target; host-resolved `path` | sanctioned resolved file path; target root for canonical handle; byte limit argument | instance root, UUID, state, registry, governance |
| `write_file` | apply; reads/writes target; host-resolved `path` | sanctioned resolved path; content/confirmation arguments; target root for handle | instance root, UUID, state, registry, authority policy |
| `inventory` | observe; reads target | target root; excluded roots; limit; relative-handle helper | instance identity/UUID, state, registry, awareness |
| `search_text` | observe; reads target | target root; excluded roots; query/options; relative-handle helper | instance identity/UUID, state, registry, awareness |

Measured current coupling: all five import `core.tool_runtime.ToolContext`. That type
requires `instance_root`, `target_root`, `state_root`, and `instance_uuid`; the host sends
all four through `InstanceContext.tool_context()`. No tool body reads UUID or state. Only
inventory/search use instance-root-derived behavior, and only to exclude the host subtree.

## Host-owned responsibilities

| Responsibility | Current measured owner | T1 disposition |
|---|---|---|
| Load and verify installed identity/relative target binding | `core.instance` and CLI | Remains host-only and mandatory before dispatch |
| Resolve tool catalog and entry paths | `core.registry` / `core.contracts` | Remains host-side; mechanical tools do not import it |
| Validate caller authority and input schema | `core.control` | Remains host-only and occurs before child execution |
| Resolve declared path domains and containment | `core.containment` via control plane | Remains host-only; pass sanctioned paths/capabilities downward |
| Resolve state root and bootstrap instance state | `core.instance` / `core.storage` | Remains host-only; no current tool receives state |
| Attribute client/tool/authority and own timeout/process lifetime | `core.control` | Remains host-only |
| Validate process result/output contract and emit common envelope | `core.control` / manifests | Remains host-only; tool emits its mechanical result |

Separability must not relax these checks. A child receives less context only after the
host has established more complete truth.

## Minimum shared tool substrate

T1 will prefer one modest product-neutral context over five ceremonial bespoke classes.
The proposed substrate owns only:

- one JSON request/result subprocess convention;
- a typed mechanical context containing `target_root` and `excluded_roots`;
- an optional `state_root` only when a future manifest explicitly declares state access;
- target-relative handle and excluded-root helpers; and
- deterministic error serialization.

It does not contain or require instance UUID, instance-manifest interpretation, registry,
authority, storage bootstrap, receipts, App Journal, awareness, MCP, GUI, or tranche
machinery. `tool_root` remains a host invocation concern unless implementation evidence
shows a mechanical operation needs it. Existing `reads`/`writes` domains should drive
transport; no new manifest context vocabulary is added unless a discriminating test shows
those declarations are insufficient.

## Expected changed surfaces after approval

- `product/core/tool_runtime.py`: narrow the request protocol and context to mechanical
  facts, with no installed identity requirement.
- `product/core/instance.py`: retain full host identity while replacing/removing the
  broad child `tool_context()` projection.
- `product/core/control.py`: construct manifest-informed minimal context after all host
  validation and containment checks.
- `product/tools/*/tool.py`: consume only the product-neutral substrate without bespoke
  per-tool context classes.
- `product/tools/*/manifest.json`: strengthen machine-readable output contracts where
  current schemas prove too weak; preserve manifest ownership of operation contracts.
- `tests/`: add mechanical known-answer fixtures and host-before-child refusal witnesses;
  retain the existing real CLI acceptance walk.
- `.builder/gates/t1_mechanical_host.py`: one T1 closure gate, created only after scope
  approval, consuming product tests rather than duplicating them.
- `docs/ARCHITECTURE.md`, Current State, and later T1 journal/evidence: synchronize only
  after measured implementation.

`core.registry`, `core.contracts`, and `core.containment` remain host-owned and are changed
only if a declared acceptance witness demonstrates incidental identity coupling blocks
the seam. Factory attachment is audited as a fixture precondition but is not re-homed or
redesigned in T1.

## Completion evidence declared before implementation

The eventual T1 gate must prove all of the following through product tests and structural
checks:

1. Each tool has a manifest-owned input/output contract and a known-answer mechanical
   fixture.
2. Each tool can run through the subprocess JSON convention with product-neutral context
   that omits instance UUID and instance root; no awareness, MCP, GUI, storage, registry,
   or construction module is importable as a requirement of the mechanical layer.
3. Inventory and search exclude an explicitly transported host root without interpreting
   Sidecar identity.
4. Read/hash/write operate on host-sanctioned paths and emit correct canonical handles;
   write remains confirmation- and apply-authority-gated by the host.
5. A malicious fixture child capable of leaving a witness is not launched when instance
   identity, authority, input contract, or containment fails. This distinguishes
   host-before-child governance from a tool that merely self-refuses.
6. The installed CLI discovers the five live manifests and reaches the same control-plane
   invocation path; normal, empty, relocated, malformed-identity, traversal, absolute,
   private-subtree, and symlink fixtures remain discriminating.
7. Mechanical/runtime AST dependency checks reject imports from CLI, control, instance,
   registry, storage, receipts, journal, awareness, MCP, factory, tests, or `.builder`.
8. Observation leaves no target-owned footprint, and only explicit apply plus confirmation
   creates the intended work product.
9. A small test-only generic subprocess harness can invoke the mechanical layer without
   constructing a Sidecar instance. The harness is evidence, not a shipped generic host.
10. Canonical pytest, Ruff, T1 gate, cumulative T0 boundary checks, and one mutation or
    failure-injection witness pass with no unscored claim silently reported as PASS.

## Explicit non-goals

T1 does not implement operational receipts, App Journal, epistemic substrate, awareness,
MCP, GUI, preview/stale-approval workflow, updater/release assembly, new domain cartridges,
additional tools, standalone Tool Pack packaging, a generic production host, or maximum
per-tool context decomposition. It does not grant P3-P8 credit.

## Ordered implementation plan after approval

1. Add red/known-answer tests for product-neutral direct tool execution and host-before-
   child refusal, including an explicit mutation witness.
2. Define the smallest uniform mechanical context and JSON runner in `tool_runtime.py`.
3. Move child-context shaping into the governed host while preserving complete
   `InstanceContext` validation above it.
4. Adapt the five tools and strengthen manifest outputs only where tests require.
5. Run focused tests after each increment; preserve existing CLI/containment behavior.
6. Consolidate naming, error paths, symlink/exclusion behavior, import direction, and
   debris without absorbing T2 concerns.
7. Implement and run the authoritative T1 gate, cumulative pytest/Ruff, consumer CLI
   entrance, fresh-install/re-entry fixtures, and discovery checks.
8. Synchronize Architecture/review records, submit T1 AWAITING_APPROVAL, and stop without
   beginning T2.

## Risks and decisions held for implementation evidence

- A common context can remain appropriate; passing unused identity fields is the defect,
  not uniformity itself.
- Target-relative handles make `target_root` useful even for single-file operations.
- Excluded roots must remain path/capability facts, not a renamed instance identity API.
- Host containment followed by child file access has a potential filesystem race; T1
  preserves current safety and records any stronger race-hardening need rather than
  silently expanding scope.
- Current output schemas mostly prove only `ok`; known-answer fixtures will determine the
  minimum honest contract strengthening.
- Windows subprocess/PYTHONPATH behavior and Linux portability remain relevant, but
  sealed-artifact cross-platform certification belongs to T7.

## Review position

This declaration is submitted for operator scope review. T1 is not IMPLEMENTING. No
product change or T1 gate creation is authorized until the operator explicitly approves
this declaration.
