# Architecture Specification: Ating Universe Simulation Engine

## 1. System Context and Topology

```
┌───────────────────────────────────────────────┐
│           Vercel / Web Application            │
│         (React / Vite UI & Client)            │
└──────────────────────┬────────────────────────┘
                       │ HTTP / WebSocket / Inputs
                       ▼
┌───────────────────────────────────────────────┐
│      Python Simulation Engine (Authority)      │
│  - Continuous Logical Time Model              │
│  - Discrete Simulation Operations             │
│  - Invariant & Causality Validation           │
│  - Deterministic Execution & Scheduler        │
│  - Extension Port for AI Reasoning            │
│  - Extension Port for Persistence             │
└──────────────┬──────────────────┬─────────────┘
               │                  │
               ▼                  ▼
┌────────────────────────┐  ┌────────────────────────┐
│  Gemini AI (Optional)  │  │  Supabase PostgreSQL   │
│  Narrative / Dialogue  │  │  Durable Persistence   │
│  (Language Reasoning)  │  │  (Canonical Records)   │
└────────────────────────┘  └────────────────────────┘
```

## 2. Status Distinctions

- **VERIFIED FACT**: The existing frontend is a React/Vite web application deployed separately.
- **VERIFIED FACT**: The existing Supabase database contains `simulation_sessions`, `simulation_messages`, and `simulation_memories` (18 records).
- **DESIGN DECISION**: Python is the sole simulation authority. No state transitions, causality rules, or validation logic may reside in the frontend or directly inside database triggers.
- **DESIGN DECISION**: Gemini is an optional language reasoning component, never the simulation engine.
- **DESIGN DECISION**: The engine runs in Phase 1 with zero external network dependencies, no live database connections, and no active LLM API requirements.
- **PROVISIONAL DESIGN**: Future runtime deployments will execute the Python simulation engine as an independent service (e.g. FastAPI / worker on Railway).
- **ASSUMPTION**: Future client requests will arrive as discrete `SimulationInput` commands forwarded by the web backend.
- **OPEN QUESTION**: What specific RPC or message transport (HTTP REST, WebSockets, or message queue) will connect the web application to the Python engine in Phase 2?

## 3. Subsystem Boundaries

### 3.1 `clock`
- **Responsibility**: Manages continuous logical universe time and evaluation time windows.
- **Boundary**: Decoupled from physical wall-clock time; enforces temporal causality (`target_time >= previous_time`).

### 3.2 `contracts`
- **Responsibility**: Houses canonical domain objects (`SimulationOperation`, `WorldState`, `Agent`, `SimulationEvent`, `SimulationInput`).
- **Boundary**: Strict Pydantic models paired with machine-readable JSON schemas in `schemas/v1/`.

### 3.3 `validation`
- **Responsibility**: Multi-layered contract validation:
  1. JSON Schema Draft 2020-12 compliance.
  2. Domain invariants (e.g. state version monotonicity, non-empty IDs, energy bounds).

### 3.4 `errors`
- **Responsibility**: Standardized error hierarchy categorized by `ErrorCode` for consistent failure diagnostics and RPC responses.

### 3.5 `observability`
- **Responsibility**: Structured JSON logging contextualized with `operation_id`, `world_id`, and `state_version`.

### 3.6 `determinism`
- **Responsibility**: Controlled clocks (`DeterministicClock`) and reproducible seed management (`SeedController`) for zero-flake test environments.

### 3.7 `extensions`
- **Responsibility**: Architectural ports (`StatePersistencePort`, `OperationAuditPort`, `AIReasoningPort`) isolating external dependencies.
