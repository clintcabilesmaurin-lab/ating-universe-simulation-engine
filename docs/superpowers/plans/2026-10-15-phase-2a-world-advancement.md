# Phase 2A: Deterministic World Advancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an offline `advance_world(previous_state, operation)` operation that deterministically advances world time, dispatches registered due-event handlers, and returns a validated versioned state plus processed events.

**Architecture:** Keep execution in the existing `src/ating_engine` package. Reuse the current Pydantic contracts, `LogicalTime`, JSON Schema validation, invariant checks, and domain errors. The function is synchronous and deterministic; it does not persist state or perform network, AI, or wall-clock work.

**Tech Stack:** Python 3.11+, Pydantic 2, JSON Schema Draft 2020-12, pytest. No new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-10-15-phase-2a-world-advancement-design.md`

## Global Constraints

- **“Python remains the sole authority for state transitions.”**
- **“All tests run locally and offline.”**
- No Supabase connections, migrations, adapters, credentials, or schema changes.
- No FastAPI, worker processes, Railway, HTTP/WebSocket ingress, and deployment.
- No Gemini or other LLM calls.
- No new event generation or processing of `SimulationOperation.request.inputs`; non-empty inputs fail explicitly.
- Never mutate the caller-supplied `WorldState`, nested agents, events, or `SimulationOperation`.
- Do not introduce a local competing database or SQLite fallback.
- Leave `ating-universe-simulation-engine-old` untouched.
- Run all commands from `C:\Users\Clint Aldwin\Desktop\ating-universe-simulation-engine`.

## Review Focus

1. **Mixed naive and timezone-aware timestamps:** Interpret both through `LogicalTime` as UTC instants; never leak a Python `TypeError`.
2. **A failed handler after nested mutations:** The caller's original state and operation remain equivalently unchanged.
3. **Non-pending events and events outside the window:** Preserve them unchanged and in their original relative order.
4. **Same-time events supplied in different list orders:** Execute them in the same `(occurrence_time, event_id)` order.
5. **Domain versus unexpected handler exceptions:** Preserve an existing `EngineError`; translate an unexpected exception to `InternalEngineError` with operation context.

---

### Task 1: Repair canonical-copy repository hygiene

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Git index cleanup: tracked Python bytecode/cache artifacts only
- Reference only: `C:\Users\Clint Aldwin\Desktop\ating-universe-simulation-engine-old\.gitignore` and `.env.example`

**Interfaces:**
- No runtime interface changes.
- The backup directory is read-only for this task.

- [ ] **Step 1: Inspect the reference files and currently tracked cache paths**

  Run:
  ```powershell
  Get-Content '..\ating-universe-simulation-engine-old\.gitignore'
  Get-Content '..\ating-universe-simulation-engine-old\.env.example'
  git ls-files | Select-String '(__pycache__/|\.py[co]$)'
  ```

  Expected: reference files contain ignore patterns for Python caches, test artifacts, virtual environments and real environment files; the tracked cache list contains only bytecode/cache paths.

- [ ] **Step 2: Restore the two safe repository files into the canonical root**

  Copy or carefully reconstruct the reference `.gitignore` and placeholder-only `.env.example`. Do not copy a real `.env`, credentials, or local machine configuration.

- [ ] **Step 3: Stop tracking generated caches without deleting local working files**

  Remove only the paths identified as tracked Python bytecode/cache artifacts from the Git index (use `git rm --cached`, with force only if needed for the already-modified cache files). The new ignore rules must leave the local files in place while keeping them out of future commits.

- [ ] **Step 4: Review and commit only the hygiene change**

  Run `git diff --check`, `git diff -- .gitignore .env.example`, and inspect the staged file list before committing. Confirm no secret-like values are present.

  Commit: `chore: ignore generated Python artifacts`

**Done when:** the diff contains only the intended ignore/template additions and cache-index removals, the backup is unchanged, and the working files remain available locally.

### Task 2: Normalize logical-time invariant validation

**Files:**
- Modify: `src/ating_engine/validation/validator.py`
- Modify: `tests/test_operation_contract.py`
- Test: `tests/test_world_advancement.py` in later tasks for execution-level timestamp cases

**Interfaces:**
- Reuse `LogicalTime.from_iso8601(value).timestamp` for normalized comparisons.
- Keep `validate_operation_invariants(operation: SimulationOperation) -> None` unchanged as the public signature.

- [ ] **Step 1: Add a regression test for mixed naive and timezone-aware operation timestamps**

  Add a test to `tests/test_operation_contract.py` that creates an operation whose previous time is `2026-10-06T15:00:00` and target time is `2026-10-06T15:37:00+00:00`. Assert `validate_operation_invariants` accepts the causally valid operation.

- [ ] **Step 2: Run the focused test and verify the current bug**

  Run: `python -m pytest tests/test_operation_contract.py -q`

  Expected before the fix: the new test exposes the naive/aware comparison failure.

- [ ] **Step 3: Update operation time comparison to use the logical-time model**

  Replace direct `datetime.fromisoformat` comparisons in `validate_operation_invariants` with parsing and comparison through `LogicalTime`. Convert parse/comparison failures to the existing structured `ValidationError`; preserve the invariant that target time cannot precede previous time.

- [ ] **Step 4: Run focused validation tests**

  Run: `python -m pytest tests/test_operation_contract.py tests/test_validation.py -q`

  Expected: PASS, with malformed timestamps and backward-time operations still rejected.

- [ ] **Step 5: Commit**

  Commit: `fix: normalize logical timestamps before comparison`

### Task 3: Add the world-advancement contract and basic transition

**Files:**
- Create: `src/ating_engine/execution/__init__.py`
- Create: `src/ating_engine/execution/world_advancement.py`
- Create: `tests/test_world_advancement.py`

**Interfaces produced by this task:**

- `EventHandler = Callable[[WorldState, SimulationEvent], WorldState]`
- `AdvanceWorldResult`: frozen dataclass containing `next_state: WorldState` and `processed_events: tuple[SimulationEvent, ...]`
- `advance_world(previous_state: WorldState, operation: SimulationOperation, *, event_handlers: Mapping[str, EventHandler] | None = None) -> AdvanceWorldResult`

Export these names from `ating_engine.execution`. Keep the new module focused; do not re-export them from the package root unless a concrete existing project convention requires it.

- [ ] **Step 1: Add failing no-event and transition-validation tests**

  In `tests/test_world_advancement.py`, define small state/operation builders and cover:
  - no due events advances to target time and increments `state_version` by exactly one;
  - the input state and operation are not modified;
  - world ID mismatch, genuinely different previous logical-time instant, state-version mismatch, backward time, unsupported non-empty request inputs, and terminal operation status fail with the specified domain errors;
  - equivalent previous-time instants expressed with different UTC offsets are accepted;
  - an equal-time operation succeeds and still increments the version once.

- [ ] **Step 2: Run the new tests to confirm they fail before implementation**

  Run: `python -m pytest tests/test_world_advancement.py -q`

  Expected: collection/execution fails because the new execution interface is not implemented yet.

- [ ] **Step 3: Implement the typed result, handler type, and basic operation**

  In `world_advancement.py`, validate state and operation with their existing versioned JSON Schemas. Normalize operation/state timestamps with `LogicalTime`; verify world ID, logical-time instant, and expected state version match. Raise `InvalidStateTransitionError` for backward time before calling the existing operation invariant function, whose standalone contract continues to raise `ValidationError` for that case. Then run the relevant operation/state/domain invariant checks. Accept only `PENDING` and `RUNNING` operation status. Reject non-empty inputs instead of ignoring them. Work on deep copies and build a new state at target time with version `previous_state.state_version + 1`.

- [ ] **Step 4: Run focused tests**

  Run: `python -m pytest tests/test_world_advancement.py -q`

  Expected: all basic transition and validation tests PASS.

- [ ] **Step 5: Commit**

  Commit: `feat: add deterministic world advancement contract`

### Task 4: Dispatch due events deterministically

**Files:**
- Modify: `src/ating_engine/execution/world_advancement.py`
- Modify: `tests/test_world_advancement.py`

**Interfaces consumed:** the `EventHandler`, `AdvanceWorldResult`, and `advance_world` interface established in Task 3. Handler-map keys are event-type strings, matching `SimulationEvent.event_type`.

- [ ] **Step 1: Add failing due-event tests**

  Test chronological processing, stable `event_id` tie-breaking at equal timestamps, inclusive start/target boundaries, leaving events after the target pending, and preserving non-pending records. Also test rejection of duplicate active event IDs, stale pending events before the state's current time, and an event belonging to a different world.

- [ ] **Step 2: Run the focused tests and confirm they fail**

  Run: `python -m pytest tests/test_world_advancement.py -q`

- [ ] **Step 3: Implement event selection, ordering, dispatch, and removal**

  Validate event timestamps and event/world identity before dispatch. Select only `PENDING` events in the inclusive operation window and sort by normalized occurrence instant then lexicographic `event_id`. Invoke the registered handler for each event using a detached state snapshot set to that event's logical time and a detached event. Validate each handler result and reject modifications to engine-owned world identity, state version, logical time, or the active-event queue. Mark successfully dispatched events `PROCESSED`, return them in execution order, remove only those processed events from the final `active_events`, and preserve all other records in original relative order. Normalize the final logical time to UTC and validate the completed output state.

- [ ] **Step 4: Verify ordering and boundary behavior**

  Run: `python -m pytest tests/test_world_advancement.py -q`

  Expected: PASS, including when tied events are present in different initial list orders.

- [ ] **Step 5: Commit**

  Commit: `feat: dispatch due simulation events deterministically`

### Task 5: Harden failure atomicity and finish verification

**Files:**
- Modify: `src/ating_engine/execution/world_advancement.py`
- Modify: `tests/test_world_advancement.py`
- Optional documentation update: `docs/development-phases.md` only if it can accurately mark Phase 2A as a partial milestone without implying Phase 2's Supabase/API scope is complete

- [ ] **Step 1: Add failing handler-safety and repeatability tests**

  Cover a valid handler updating a domain field, a handler attempting to alter an engine-owned field, an unregistered due event, a handler raising an existing `EngineError`, an unexpected handler exception after nested working-state mutation, invalid handler output, and repeated equivalent executions yielding equivalent state and event order.

- [ ] **Step 2: Run the focused tests and verify missing/error-path behavior**

  Run: `python -m pytest tests/test_world_advancement.py -q`

- [ ] **Step 3: Implement fail-closed handler error behavior**

  Preserve raised `EngineError` subclasses. Convert unexpected non-domain handler exceptions to `InternalEngineError` with `operation_id` context. Raise `InvalidStateTransitionError` for a due event without a handler or a handler that alters protected envelope fields. Validate handler/final agents and state invariants. Ensure the caller's original nested state, events, and operation remain unchanged on every failure; never return a partial result.

- [ ] **Step 4: Run the complete offline test suite**

  Run: `python -m pytest -q`

  Expected: the new execution tests pass and all 40 pre-existing Phase 1 tests remain green. No network access or secrets should be required.

- [ ] **Step 5: Review repository status and final diff**

  Run `git diff --check`, `git status --short`, and inspect each staged diff. Confirm generated caches are ignored/untracked locally, no runtime dependencies were added, and there are no Supabase/API/LLM changes. Do not push or deploy as part of this plan.

- [ ] **Step 6: Commit the verified feature**

  Commit: `test: verify deterministic world advancement` or use a feature-appropriate message if the final staged changes are primarily implementation.

## Completion Checklist

- [ ] Repository preflight is committed independently and the backup is unchanged.
- [ ] `advance_world` contract and event behavior match the approved Phase 2A specification.
- [ ] Every event handler is explicit, deterministic, and isolated from caller-owned inputs.
- [ ] Existing Phase 1 tests remain green alongside the new execution tests.
- [ ] No database, network, LLM, service, or deployment work is included.
