# Architectural Decisions Record: Ating Universe Simulation Engine

## Decision Log

### ADR-001: Python as Sole Simulation Authority
- **Status**: DESIGN DECISION
- **Context**: The existing ecosystem has a React/Vite web application and a Supabase PostgreSQL database. LLMs (Gemini) are planned for conversational intelligence.
- **Decision**: All state transition logic, scheduling, causality validation, probability models, and event resolution reside exclusively in the Python engine. Neither the web frontend nor Supabase stored procedures nor Gemini prompts will serve as the source of truth for simulation state transitions.
- **Consequences**: Ensures verifiable determinism, robust testing, and isolation of simulation mechanics from user interface and LLM hallucinations.

### ADR-002: Continuous Logical Time with Discrete Evaluation Operations
- **Status**: DESIGN DECISION
- **Context**: Simulation needs realistic pacing without wasting compute on empty seconds.
- **Decision**: The simulation universe has continuous logical world time, but computation occurs discretely via bounded operations (`previous_logical_time -> target_logical_time`). There is no perpetual 1-second tick loop.
- **Consequences**: Time can advance flexibly (e.g. 37 minutes in a single operation), enabling event-driven scheduling and low server idle costs.

### ADR-003: Operation Contract as the Foundational Unit of Work
- **Status**: DESIGN DECISION
- **Context**: Concurrent web requests, user messages, and scheduled intervals can trigger engine executions.
- **Decision**: Define `SimulationOperation` containing `operation_id`, `world_id`, `previous_logical_time`, `target_logical_time`, `previous_state_version`, request metadata (idempotency key), and result metadata.
- **Consequences**: Supports future optimistic concurrency control, auditability, idempotency deduplication, and replayability.

### ADR-004: Dual-Layer Validation (JSON Schema + Python Domain Invariants)
- **Status**: DESIGN DECISION
- **Context**: Contracts must be machine-readable across system boundaries (TypeScript client/Vercel) while enforcing deep semantic business rules.
- **Decision**: JSON Schema Draft 2020-12 defines data structure boundaries across processes; Python models and invariant checkers enforce runtime business logic (monotonic versioning, causal time progression).
- **Consequences**: Shared schemas can be exported to frontend tooling; invalid inputs are caught at the boundary before affecting state.

### ADR-005: Decoupled Architectural Ports for Supabase and Gemini
- **Status**: DESIGN DECISION
- **Context**: Supabase and Gemini are future integration partners, but coupling them to the core engine would break testability and offline development.
- **Decision**: Abstract `StatePersistencePort`, `OperationAuditPort`, and `AIReasoningPort` interfaces. Provide mock/ephemeral implementations in the core codebase.
- **Consequences**: Engine core tests run with zero network activity and 100% determinism.

### ADR-006: No Local Competing Database (Zero SQLite Fallback)
- **Status**: DESIGN DECISION
- **Context**: Developers sometimes inject SQLite as a local mock for Supabase.
- **Decision**: Do not create a competing local database or SQLite fallback layer. In-memory ephemeral adapters are used strictly for unit testing. Canonical durable persistence is Supabase.
- **Consequences**: Prevents divergence between local SQLite behavior and production PostgreSQL/Supabase queries.

### ADR-007: Existing Web App Tables vs Future Engine Persistence Schema
- **Status**: VERIFIED FACT & OPEN QUESTION
- **Verified Fact**: Supabase currently hosts `simulation_sessions`, `simulation_messages`, and `simulation_memories` (18 records).
- **Open Question**: Will Phase 2 map the engine's `WorldState` snapshot directly into JSONB columns in `simulation_sessions`, or will normalized tables be introduced via additive migrations?
- **Decision**: Defer all database schema modifications to Phase 2. Phase 1 defines engine contracts only.
