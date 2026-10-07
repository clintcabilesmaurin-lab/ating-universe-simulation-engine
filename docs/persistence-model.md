# Persistence Model: Ating Universe Simulation Engine

## 1. Durable Persistence Architecture

Canonical durable persistence will reside in Supabase (PostgreSQL).

```
┌─────────────────────────────────┐
│    Python Simulation Engine     │
└───────────────┬─────────────────┘
                │ StatePersistencePort / OperationAuditPort
                ▼
┌─────────────────────────────────┐
│     Supabase (PostgreSQL)       │
│  - Session / World State Snapshots
│  - Operation Audit Trail        │
│  - Event Log                    │
│  - Memories (Phase 3)           │
└─────────────────────────────────┘
```

## 2. Status Distinctions

- **VERIFIED FACT**: Supabase currently contains three existing tables: `simulation_sessions`, `simulation_messages`, and `simulation_memories` (18 records).
- **VERIFIED FACT**: These existing tables belong to the current React/Vite web application architecture.
- **DESIGN DECISION**: In Phase 1, the engine does not connect to Supabase, run migrations, or alter database schemas.
- **DESIGN DECISION**: Do not create a competing local database or use SQLite as a fallback. An in-memory port (`InMemoryEphemeralPersistence`) satisfies test execution.
- **PROVISIONAL DESIGN**: Future persistence will store versioned state snapshots alongside an append-only operations audit log for full event sourcing / replayability.
- **ASSUMPTION**: State snapshots can be stored as structured JSONB documents indexed by `(world_id, state_version)`.
- **OPEN QUESTION**: Should historical state snapshots be pruned or archived to keep PostgreSQL table size bounded over millions of steps?
- **OPEN QUESTION**: How will the existing 18 records in `simulation_memories` map to the Phase 3 memory extraction model?

## 3. Persistence Ports

Phase 1 establishes the contracts:
- `StatePersistencePort`:
  - `save_state_snapshot(state: WorldState) -> None`
  - `load_latest_state(world_id: str) -> Optional[WorldState]`
  - `load_state_version(world_id: str, version: int) -> Optional[WorldState]`
- `OperationAuditPort`:
  - `record_operation(operation: SimulationOperation) -> None`
  - `get_operation(operation_id: str) -> Optional[SimulationOperation]`
