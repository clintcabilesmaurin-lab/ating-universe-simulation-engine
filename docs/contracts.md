# Boundary Contracts Specification: Ating Universe Simulation Engine

## 1. Boundary Overview

Contracts define the strict communication schema between external clients, internal subsystems, durable persistence, and optional language reasoning models.

```
External (Vercel / CLI) ──────────► SimulationInput ─────────► Engine Boundary
                                                                    │
State Persistence (Supabase) ◄───── WorldState Snapshot ◄──────────┤
                                                                    │
Audit Log (Supabase) ◄───────────── SimulationOperation ◄──────────┤
                                                                    │
Event Stream / History ◄─────────── SimulationEvent ◄──────────────┤
                                                                    │
Language Reasoning (Gemini) ◄────── AIReasoningPort ◄───────────────┘
```

## 2. Status Distinctions

- **VERIFIED FACT**: Contracts are machine-readable via versioned JSON Schemas in `src/ating_engine/schemas/v1/`.
- **DESIGN DECISION**: External user inputs (`SimulationInput`) cannot mutate state directly; they must enter the engine through an operational request.
- **DESIGN DECISION**: State updates are versioned monotonically (`state_version`) to enable optimistic concurrency checks.
- **PROVISIONAL DESIGN**: `SimulationOperation` acts as the transaction unit for discrete simulation advances.
- **ASSUMPTION**: Clients will supply an `idempotency_key` on retryable input submissions.
- **OPEN QUESTION**: What maximum payload size limit should be enforced on arbitrary `payload` and `custom_attributes` dictionaries in production?

## 3. Core Contract Definitions

### 3.1 `SimulationOperation`
- **Schema ID**: `https://ating.universe/schemas/v1/operation.schema.json`
- **Purpose**: Encapsulates a discrete transition of the universe from `previous_logical_time` to `target_logical_time`.
- **Key Fields**:
  - `operation_id`: UUID string.
  - `world_id`: World / timeline identifier.
  - `engine_version`: Engine semantic version.
  - `schema_version`: Schema contract version (`1.0.0`).
  - `previous_logical_time`: ISO-8601 UTC timestamp.
  - `target_logical_time`: ISO-8601 UTC timestamp.
  - `previous_state_version`: Integer version check (optimistic lock).
  - `status`: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `ABORTED`.
  - `request`: Contains `idempotency_key`, `inputs`, `requested_by`.
  - `result`: Contains `target_state_version`, `events_generated_count`, `events_processed_count`, `execution_duration_ms`, `error`.
  - `created_at`, `completed_at`: Physical wall-clock UTC timestamps.

### 3.2 `WorldState`
- **Schema ID**: `https://ating.universe/schemas/v1/state.schema.json`
- **Purpose**: Canonical snapshot of the world at a specific logical time.
- **Key Fields**:
  - `world`: `WorldIdentity` (`world_id`, `name`, `timeline_id`).
  - `state_version`: Integer monotonically increasing from 0.
  - `logical_time`: ISO-8601 UTC timestamp.
  - `agents`: Map of `agent_id -> Agent`.
  - `active_events`: List of pending or unresolved `SimulationEvent` objects.
  - `environment`: `EnvironmentState` (`weather`, `ambient_context`, `variables`).
  - `metadata`: Arbitrary engine metadata.

### 3.3 `Agent`
- **Schema ID**: `https://ating.universe/schemas/v1/agent.schema.json`
- **Purpose**: Representation of an entity/agent inside the simulated universe.
- **Key Fields**:
  - `identity`: `AgentIdentity` (`agent_id`, `name`, `archetype`).
  - `status`: `ACTIVE`, `INACTIVE`, `DORMANT`, `ARCHIVED`.
  - `state`: `AgentState` (`location`, `mood`, `energy`, `custom_attributes`).
  - `schedule`: `AgentScheduleReference` (pointers to schedule/activity).
  - `traits`: `AgentTraitsReference` (pointers to trait profiles).
  - `needs`: `AgentNeedsReference` (metrics map).
  - `relationships`: `AgentRelationshipsReference` (ties to other agents).
  - `memory`: `AgentMemoryReference` (cluster ID, memory references count).

### 3.4 `SimulationEvent`
- **Schema ID**: `https://ating.universe/schemas/v1/event.schema.json`
- **Purpose**: Represents an event occurring at a specific logical time.
- **Key Fields**:
  - `event_id`: UUID string.
  - `world_id`: World identifier.
  - `event_type`: Category identifier (`SYSTEM`, `AGENT_ACTION`, `ENVIRONMENTAL`, `INTERACTION`, `EXTERNAL_INPUT`).
  - `occurrence_time`: ISO-8601 UTC logical timestamp.
  - `status`: `PENDING`, `PROCESSING`, `PROCESSED`, `CANCELLED`, `FAILED`.
  - `payload`: Domain data.
  - `provenance`: Origin tracking (`source_id`, `source_type`, `correlation_id`, `created_at`).

### 3.5 `SimulationInput`
- **Schema ID**: `https://ating.universe/schemas/v1/input.schema.json`
- **Purpose**: Clean ingress boundary for user messages and external triggers.
- **Key Fields**:
  - `input_id`: UUID string.
  - `world_id`: Target world.
  - `kind`: `USER_MESSAGE`, `COMMAND`, `INJECTION`, `SYSTEM_TRIGGER`.
  - `content`: Textual command or message body.
  - `target_agent_id`: Optional target agent.
  - `provenance`: `sender_id`, `origin_platform`, `received_at`.
