# Ating Universe Simulation Engine

Python simulation authority for the Ating Universe.

## Overview

The `ating-universe-simulation-engine` is the authoritative core that governs state transitions, causal time advancement, scheduling, probability, event resolution, and agent behaviors for the Ating Universe.

In the target system:
```
Vercel / Web Application  (React / Vite UI & Client)
           ↓
Python Simulation Engine  (Authoritative Simulation Core)
           ↓
  Supabase PostgreSQL    (Durable Canonical Persistence)
```
with Google Gemini serving as an optional AI reasoning and language synthesis component inside the Python engine.

## Phase 1 Scope & Principles

Phase 1 establishes the technical foundations and architectural contracts:
- **Python is the simulation authority**: State transitions, causal rules, and schedules belong strictly in Python.
- **Continuous logical time, discrete computation**: Logical world time is continuous; evaluation occurs across discrete bounded operations. No perpetual 1-second loop.
- **Strict boundary separation**: Distinguishes external inputs (`SimulationInput`) from authoritative internal state (`WorldState`).
- **Dual-layer validation**: Versioned JSON Schemas (Draft 2020-12) paired with Python invariant enforcement.
- **No external dependencies in foundation**: Runs autonomously without network access, Supabase connections, or LLM API keys.
- **Zero competing databases**: No local SQLite fallback; Supabase is the sole planned production persistence.

## Directory Structure

```
ating-universe-simulation-engine/
├── docs/                      # Architectural documentation
│   ├── architecture.md        # System boundaries & topology
│   ├── decisions.md           # Architecture Decision Records (ADRs)
│   ├── contracts.md           # Boundary specifications
│   ├── simulation-model.md    # Conceptual time & step model
│   ├── persistence-model.md   # Supabase persistence strategy & open questions
│   ├── ai-boundary.md         # Relationship between Python & Gemini
│   └── development-phases.md  # Roadmap across Phases 1 - 5
├── src/
│   └── ating_engine/
│       ├── clock/             # Logical time and continuous windows
│       ├── config/            # Runtime settings and environment boundary
│       ├── contracts/         # Core domain contracts (Operation, State, Agent, Event, Input)
│       ├── determinism/       # Deterministic clock and seed controller
│       ├── errors/            # Standardized domain error hierarchy
│       ├── extensions/        # Abstract ports for Supabase & Gemini
│       ├── observability/     # Structured JSON logging & operation context
│       ├── schemas/           # Machine-readable JSON Schemas (v1)
│       ├── validation/        # Schema validator & invariant checkers
│       └── version.py         # Engine and schema version definitions
├── tests/                     # Foundational test suite
├── .env.example               # Safe environment variable template
├── pyproject.toml             # Project packaging & tool configuration
├── requirements.txt           # Pinned dependencies
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.11+ (Python 3.13 supported)

### Installation
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Unix / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests
```bash
pytest
```
All unit tests run completely offline and verify contract schemas, validation invariants, configuration boundaries, error handling, determinism, and structured logging.
