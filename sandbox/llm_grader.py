"""
Sandbox - LLM Grader Placeholder
================================
Placeholder untuk fitur LLM Agent Grader yang akan dikembangkan.

Fitur Rencana:
- Mode Thinking: LLM akan mengevaluasi relevansi hasil pencarian
- Auto-grading: Score dari semantic search + LLM judgment
- Reasoning Chain: Penjelasan mengapa jawaban cocok/tidak
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class GradeResult:
    """Hasil grading dari LLM."""
    score: float  # 0.0 - 1.0
    is_relevant: bool
    reasoning: str
    confidence: float


class BaseLLMGrader(ABC):
    """Abstract base class untuk LLM Grader."""
    
    @abstractmethod
    def grade(self, query: str, answer: str, context: Optional[str] = None) -> GradeResult:
        """
        Grade relevansi jawaban terhadap query.
        
        Args:
            query: Pertanyaan user
            answer: Jawaban dari FAQ
            context: Konteks tambahan (opsional)
            
        Returns:
            GradeResult dengan score dan reasoning
        """
        pass
    
    @abstractmethod
    def batch_grade(self, items: list[tuple[str, str]]) -> list[GradeResult]:
        """Grade multiple query-answer pairs."""
        pass


class PlaceholderGrader(BaseLLMGrader):
    """
    Placeholder implementation - always returns neutral score.
    Replace with actual LLM implementation later.
    """
    
    def grade(self, query: str, answer: str, context: Optional[str] = None) -> GradeResult:
        return GradeResult(
            score=0.5,
            is_relevant=True,
            reasoning="[Placeholder] LLM Grader belum diimplementasi.",
            confidence=0.0
        )
    
    def batch_grade(self, items: list[tuple[str, str]]) -> list[GradeResult]:
        return [self.grade(q, a) for q, a in items]


# Future implementations:
# class GeminiGrader(BaseLLMGrader): ...
# class OpenAIGrader(BaseLLMGrader): ...
# class LocalLLMGrader(BaseLLMGrader): ...


def get_grader(provider: str = "placeholder") -> BaseLLMGrader:
    """Factory function untuk mendapatkan grader."""
    graders = {
        "placeholder": PlaceholderGrader,
        # "gemini": GeminiGrader,
        # "openai": OpenAIGrader,
    }
    return graders.get(provider, PlaceholderGrader)()
