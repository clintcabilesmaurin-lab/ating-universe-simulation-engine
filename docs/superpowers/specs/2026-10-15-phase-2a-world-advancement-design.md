# Phase 2A Design Specification: Deterministic World Advancement

**Status:** Draft for user review  
**Date:** 2026-10-15  
**Repository:** `clintcabilesmaurin-lab/ating-universe-simulation-engine`  
**Working copy:** `C:\Users\Clint Aldwin\Desktop\ating-universe-simulation-engine`

## 1. Purpose

Add the first executable simulation operation to the existing Python engine. Given a validated prior `WorldState` and a `SimulationOperation`, the engine advances logical world time in one bounded operation, dispatches due events in a deterministic order, and returns a new versioned state plus the processed event records.

This is an offline foundation for the persistent Ating Universe simulation, not a complete agent-behavior system. Python remains the sole authority for state transitions. The React client, database, and any language model must not independently mutate authoritative state.

## 2. Scope

### Included

- A pure, deterministic core operation with a typed result.
- Contract validation and cross-checks between the operation and its input state.
- Causal logical-time advancement, including equal-time operations.
- Deterministic selection and ordering of due events.
- A small explicit event-handler interface so event effects are defined by registered Python handlers, not guessed from arbitrary payload dictionaries.
- New immutable-by-convention output state with a monotonically incremented version.
- Offline tests for successful operations, event order, failure behavior, input immutability, and repeatability.

### Explicitly excluded

- Supabase connections, migrations, adapters, credentials, or schema changes.
- FastAPI, worker processes, Railway, HTTP/WebSocket ingress, and deployment.
- Gemini or other LLM calls.
- Persistent idempotency records, database optimistic locking, and concurrent request handling.
- Agent cognition, schedules, autonomous motivation, relationship logic, memory retrieval, dialogue generation, or new domain-specific event payload schemas.
- Generating new events from a handler in this first cut.
- Processing `SimulationOperation.request.inputs`. Until input-to-event semantics are designed, non-empty operation inputs must be rejected explicitly rather than silently ignored.

## 3. Public Contract

Expose a core function conceptually equivalent to:

```python
advance_world(
    previous_state: WorldState,
    operation: SimulationOperation,
    *,
    event_handlers: Mapping[str, EventHandler] | None = None,
) -> AdvanceWorldResult
```

`AdvanceWorldResult` contains:

- `next_state: WorldState`: the resulting world snapshot at the target logical time.
- `processed_events: tuple[SimulationEvent, ...]`: successfully dispatched event records marked `PROCESSED`, in execution order.

The handler map is an explicit dependency-injection seam. A handler receives the working state at that event's occurrence time and the event, then returns the resulting working state. Handlers must be deterministic and side-effect-free: no network calls, persistence, wall-clock-dependent decisions, random unseeded behavior, or mutation of the original input objects. The engine validates each handler result, including world-state and agent invariants, and protects envelope fields that the engine owns. The handler may update domain fields such as agents, environment, or metadata; the handler may not change world identity, state version, logical time, or the active-event queue.

The function accepts operation statuses `PENDING` and `RUNNING` only. It does not mutate the operation or manage its lifecycle; the caller remains responsible for marking an operation `COMPLETED`, `FAILED`, or `ABORTED`. Terminal-status operations are rejected to prevent accidental re-execution.

If a due event has no registered handler, execution fails closed. The operation must not advance the world past an unhandled event or silently mark the event complete. If a handler or validation fails, no result is returned and the supplied input state remains unchanged.

## 4. Execution Rules

1. Validate the input state and operation using the existing versioned JSON Schema and Python invariant facilities.
2. Parse logical timestamps through the existing logical-time model and compare normalized UTC instants. Preserve the project's current behavior for naive timestamps, which treats them as UTC.
3. Confirm that `operation.world_id` matches `previous_state.world.world_id`.
4. Confirm that the operation's previous logical time represents the same instant as `previous_state.logical_time`.
5. Confirm that `operation.previous_state_version == previous_state.state_version`. A version mismatch is a concurrency conflict, not a silent overwrite.
6. Require `operation.target_logical_time >= operation.previous_logical_time`.
7. Reject any non-empty `operation.request.inputs` in this phase because input interpretation is not yet implemented.
8. Validate active-event identity and timestamps. Duplicate active `event_id` values and pending events older than the state's current logical time are invalid input state, not events to skip.
9. Select pending events in the inclusive window `[previous_logical_time, target_logical_time]`. Sort them by normalized UTC `occurrence_time`, then lexicographically by `event_id` as a stable tie-breaker.
10. Dispatch each event in that order. For each handler call, provide an isolated, normalized working state whose logical time is the event's occurrence time. After a handler succeeds and its returned state is validated, mark that event `PROCESSED` in the engine-owned working queue before invoking the next handler. A handler may observe earlier due events as `PROCESSED`, the current event as `PENDING`, and later due events as `PENDING`; it may not change world identity, state version, logical time, or the active-event queue. Validate the returned state and ensure the handler did not change engine-owned envelope fields.
11. Mark each successfully handled event `PROCESSED` and return it in `processed_events`. Remove those processed records from `next_state.active_events`; preserve events outside the window and non-pending event records unchanged.
12. Set `next_state.logical_time` to `operation.target_logical_time` in canonical UTC format and set `next_state.state_version` to `previous_state.state_version + 1`.
13. Validate the final state before returning the result.

An equal-time operation is valid. It can process pending events exactly at that instant; otherwise it still creates one new versioned operation result. A call with no due events returns an empty `processed_events` tuple.

## 5. Determinism and State Safety

Given equivalent input state, operation, and equivalent pure handlers, execution must produce equivalent output state and event order. Do not use physical wall-clock time, unseeded randomness, iteration order of unordered collections, network results, or LLM output to decide simulation outcomes.

Before JSON normalization, validate source values against their declared field types without coercion. Serializer warnings are errors. Reject non-finite numbers, non-string object keys, binary values, cyclic values, and unordered sets/frozensets rather than silently changing or reordering them. Tuples and date/time values may be normalized intentionally to JSON arrays and ISO-8601 strings, respectively.

Treat the caller-supplied state and operation as read-only. Work on deep copies where needed. A failure must not leave the supplied `WorldState`, its nested agents, or event objects partially modified.

The current event-handler boundary does not infer behavior from an unknown payload. Domain-specific effects belong in explicit handlers and are outside the built-in scope of this first slice. Event generation and recursive processing of newly generated events require a later design.

## 6. Errors

Reuse the existing domain error hierarchy:

- `ValidationError` for malformed contracts, unsupported non-empty inputs, duplicate event IDs, invalid timestamps, or invalid handler output.
- `ConcurrencyConflictError` when the operation's expected state version does not match the supplied state.
- `InvalidStateTransitionError` for world/time mismatches, backward time, stale pending events, missing event handlers, terminal-status operations, or a handler that attempts to alter engine-owned envelope fields.
- `InternalEngineError` when a handler raises an unexpected non-domain exception; preserve existing `EngineError` subclasses rather than obscuring their meaning.

Use structured details and `operation_id` when available. Do not swallow failures, skip an unhandled due event, or return a partial next state.

## 7. Testing and Acceptance Criteria

All tests run locally and offline. No Supabase project, environment secrets, Railway service, or AI API key is required.

Required test coverage:

- A basic no-event operation advances logical time and increments the state version exactly once.
- Backward time, mismatched world ID, mismatched previous logical time, and state-version mismatch fail with the expected domain error.
- Due events execute in chronological order, with `event_id` as the stable tie-breaker for equal timestamps.
- Events on either inclusive boundary are eligible; events after target time remain pending.
- A pending event older than the current state time is rejected; duplicate active event IDs are rejected.
- Equal-time operations are supported.
- Non-empty operation inputs and terminal-status operations are rejected clearly.
- Missing handlers fail closed and do not advance time or consume the event.
- A handler can produce a valid domain-state update, while attempts to modify engine-owned envelope fields are rejected; unexpected handler exceptions become structured internal engine errors.
- Handler failure or final validation failure leaves the caller's input state and nested objects unchanged.
- Repeating execution with the same initial state, operation, and deterministic handler produces equivalent results.
- Existing Phase 1 tests remain green.

**Done means:** the new focused test suite passes, all 40 existing Phase 1 tests continue to pass, the operation runs without network access, and no database/API/LLM work is introduced by this slice.

## 8. Repository Preflight

Before runtime code changes, restore or carefully reconstruct the missing root `.gitignore` and safe `.env.example` in the canonical working copy, using the verified `ating-universe-simulation-engine-old` folder as reference. Review their diff, keep actual secrets out of source control, and leave the backup folder untouched. This is repository hygiene, separate from the runtime feature.

## 9. Implementation Boundary

The implementation plan must keep the first slice inside the existing `src/ating_engine` package and its pytest suite. Prefer small modules with one responsibility and reuse the current contracts, logical-time model, error hierarchy, and validation utilities. Do not introduce new runtime dependencies unless the implementation plan identifies a concrete need and gets review.

After this written specification is approved, the next artifact is an implementation plan. No runtime implementation is authorized by approval of this specification alone.