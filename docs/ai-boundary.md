# AI Integration Boundary: Python Engine and Gemini

## 1. System Relationship

```
┌────────────────────────────────────────────────────────┐
│               Python Simulation Engine                 │
│                 (Sole Rule Authority)                  │
│                                                        │
│  - Determines state transitions                        │
│  - Enforces schedules, physical limits, and causality │
│  - Calculates probabilities and event triggers         │
│  - Validates and approves agent actions                │
└──────────────────────────┬─────────────────────────────┘
                           │ Invokes AI for qualitative tasks
                           │ (reflection, dialogue, nuance)
                           ▼
┌────────────────────────────────────────────────────────┐
│                     Gemini API                         │
│              (Language & Reasoning Port)               │
│                                                        │
│  - Does NOT alter state directly                       │
│  - Does NOT schedule events autonomously               │
│  - Emits candidate dialogue / thoughts                 │
│  - Subject to Python validation and rejection          │
└────────────────────────────────────────────────────────┘
```

## 2. Status Distinctions

- **VERIFIED FACT**: Gemini is an LLM service accessed via external network APIs.
- **DESIGN DECISION**: Python is the simulation authority. Gemini must NEVER become the simulation engine.
- **DESIGN DECISION**: The engine can execute its core simulation logic completely without Gemini, LLM APIs, or network access.
- **DESIGN DECISION**: When Gemini is enabled in future phases, its outputs are treated as untrusted candidates that must pass Python validation before state mutation.
- **PROVISIONAL DESIGN**: Gemini will be called across the `AIReasoningPort` for agent inner monologues, subjective memory reflections, and natural dialogue synthesis.
- **ASSUMPTION**: Prompt templates and structured JSON response schemas will constrain Gemini outputs to parseable payloads.
- **OPEN QUESTION**: What token budget and timeout policy will govern Gemini API invocations during real-time user chat interactions?
- **OPEN QUESTION**: How will rate limits or network outages from Gemini be gracefully degraded without pausing the logical universe?

## 3. Extension Interface

The architectural port is established in `ating_engine.extensions.ai`:
```python
class AIReasoningPort(ABC):
    @abstractmethod
    def evaluate_agent_reflection(self, agent: Agent, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_dialogue_candidate(self, speaker: Agent, recipient: Agent, context: Dict[str, Any]) -> str:
        pass
```
The test suite utilizes `MockAIProvider`, confirming zero network calls are required for engine execution.
