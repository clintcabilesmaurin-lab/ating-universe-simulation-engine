# Development Roadmap: Phase 1 through Phase 5

## 1. Roadmap Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Phase 1    │────►│   Phase 2    │────►│   Phase 3    │────►│   Phase 4    │────►│   Phase 5    │
│ Foundations  │     │  Execution & │     │    Memory    │     │ Autonomous   │     │ Scale, Web   │
│ & Contracts  │     │ Persistence  │     │ Architecture │     │ Intelligence │     │ Integration  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## 2. Phase Breakdown

### Phase 1: Foundation and Architectural Contracts (Current Phase)
- **Status**: COMPLETE
- **Deliverables**:
  - Python package structure (`src/ating_engine`).
  - Architectural documentation and decisions records.
  - Domain contracts: `SimulationOperation`, `WorldState`, `Agent`, `SimulationEvent`, `SimulationInput`.
  - Versioned JSON Schemas (Draft 2020-12) in `schemas/v1/`.
  - Dual-layer validation (JSON Schema + Python domain invariants).
  - Categorized error model (`ErrorCode`, `EngineError`).
  - Structured JSON logging (`OperationLoggingContext`).
  - Deterministic testing utilities (`DeterministicClock`, `SeedController`).
  - Architectural extension ports for Supabase and Gemini.
  - Comprehensive passing pytest suite.

### Phase 2: Execution Engine, Time-Advancement, and Supabase Persistence
- **Status**: FUTURE
- **Scope**:
  - Implement concrete operational time-advancement algorithm (`previous_time -> target_time`).
  - Implement causal event queue and event dispatcher.
  - Connect concrete `SupabasePersistenceAdapter` using Supabase Python client.
  - Implement optimistic concurrency locking and idempotency tracking on Supabase.
  - Ingress API (FastAPI / worker endpoint) to receive `SimulationInput` from web tier.

### Phase 3: Memory Architecture and NotebookLM Corpus Integration
- **Status**: FUTURE
- **Scope**:
  - Design canonical memory data model (episodic, semantic, relational).
  - NotebookLM / corpus extraction pipeline for Messenger conversation archives.
  - Agent memory indexing and retrieval mechanisms (recency, importance, relevance).
  - Seed historical memories for primary agents (Clint, Maica).

### Phase 4: Agent Cognition, Needs, and Gemini AI Language Integration
- **Status**: FUTURE
- **Scope**:
  - Implement concrete `GeminiAIProvider` implementing `AIReasoningPort`.
  - Agent motivation, diurnal schedules, emotional valence, and relationship dynamics.
  - Dialogue candidate generation with Python safety/context filtering.
  - Probabilistic decision making and action selection.

### Phase 5: Web Application Integration, Polish, and Production Deployment
- **Status**: FUTURE
- **Scope**:
  - End-to-end integration with the React/Vite web application.
  - Live simulation session management and real-time streaming updates.
  - Production deployment (Railway / containerized service).
  - Performance profiling, long-horizon stress testing, and observability telemetry.
