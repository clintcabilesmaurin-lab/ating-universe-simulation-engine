"""Extension points and architectural ports for optional AI integration (Gemini).

Defines the boundary between Python simulation authority and external LLMs.
The engine remains fully functional when AI is disabled or unavailable.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ating_engine.contracts.agent import Agent


class AIReasoningPort(ABC):
    """Abstract interface for delegating language generation and narrative evaluation to an LLM."""

    @abstractmethod
    def evaluate_agent_reflection(self, agent: Agent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-level psychological reflection for an agent."""
        pass

    @abstractmethod
    def generate_dialogue_candidate(
        self,
        speaker: Agent,
        recipient: Agent,
        context: Dict[str, Any],
    ) -> str:
        """Generate candidate dialogue utterance between agents."""
        pass


class MockAIProvider(AIReasoningPort):
    """Deterministic mock provider used in testing and offline environments.

    Ensures zero network access and deterministic test output.
    """

    def __init__(self, fixed_dialogue: str = "Hello.", fixed_reflection: Optional[Dict[str, Any]] = None) -> None:
        self.fixed_dialogue = fixed_dialogue
        self.fixed_reflection = fixed_reflection or {"mood_shift": "neutral", "summary": "Pondered existence."}

    def evaluate_agent_reflection(self, agent: Agent, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"agent_id": agent.identity.agent_id, **self.fixed_reflection}

    def generate_dialogue_candidate(
        self,
        speaker: Agent,
        recipient: Agent,
        context: Dict[str, Any],
    ) -> str:
        return f"[{speaker.identity.name} -> {recipient.identity.name}]: {self.fixed_dialogue}"
