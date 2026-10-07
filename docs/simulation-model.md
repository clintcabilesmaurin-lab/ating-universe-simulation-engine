# Simulation Model: Ating Universe Simulation Engine

## 1. Conceptual Model

The simulation engine models the dynamic life and interpersonal reality of the Ating Universe.

```
       Logical Timeline (Continuous)
───┼───────────────────────────────┼────────────────────────►
   │                               │
 t_start = 15:00                t_target = 15:37
 (State Version N)              (State Version N+1)
        │                               ▲
        └───────[ Simulation ]──────────┘
                [ Operation  ]
                - Resolve inputs
                - Advance schedule
                - Process scheduled events
                - Update agent states
```

## 2. Status Distinctions

- **VERIFIED FACT**: Physical servers run asynchronously and intermittent client connections trigger updates.
- **DESIGN DECISION**: Continuous logical world time with discrete computation steps. No perpetual 1-second loop.
- **DESIGN DECISION**: Causality is strictly enforced: `target_logical_time >= previous_logical_time`.
- **PROVISIONAL DESIGN**: An operation advances the world across a `TimeWindow`, resolving intermediate scheduled events in causal chronological order.
- **ASSUMPTION**: Agents have diurnal schedules and routines that can be projected forward over arbitrary time deltas (e.g. 15 minutes, 37 minutes, or 8 hours).
- **OPEN QUESTION**: How will fine-grained conversational pacing (e.g. rapid back-and-forth dialogue exchanges) be subdivided when advancing across large time windows?

## 3. Time Progression Rules

1. **Logical vs Physical Time**:
   - `LogicalTime`: Continuous point in the fictional universe timeline. All representations are UTC ISO-8601 strings or timezone-aware Python datetimes.
   - `Physical Time`: Actual wall-clock time on the executing host. Recorded only for auditing, latency measurement, and input receipt.

2. **Step Evaluation**:
   - An operation receives `WorldState(v_n)` at `t_prev`.
   - The operation resolves any pending events between `[t_prev, t_target]`.
   - The operation applies external `SimulationInput` instances assigned to this window.
   - A new immutable `WorldState(v_{n+1})` is produced at `t_target`.
