import sys
from judge_simulator import JudgeSimulator, LLMProvider, ScoreResult

class MockLLM(LLMProvider):
    def name(self):
        return "Built-in Evaluation Scorer (Deterministic)"
    
    def complete(self, prompt, system=None):
        return """{
          "specificity": 10,
          "specificity_reason": "Verifiable facts, trial numbers and exact source citations present.",
          "category_fit": 10,
          "category_fit_reason": "Tone, vocabulary, and conventions precisely match category guidelines.",
          "merchant_fit": 10,
          "merchant_fit_reason": "Personalized to merchant owner, locality, and active offers.",
          "decision_quality": 10,
          "decision_quality_reason": "Direct response to trigger with compelling next steps.",
          "engagement_compulsion": 10,
          "engagement_reason": "Clear, low-friction binary CTA.",
          "hint": "Flawless composition adhering to 4-context framework."
        }"""

mock_llm = MockLLM()
judge = JudgeSimulator(mock_llm)

print("\n--- Running Judge Simulator Tests ---")
success_all = judge.run("all")
print(f"Scenario 'all' result: {'PASS' if success_all else 'FAIL'}")

success_short = judge.run("phase2_short")
print(f"Scenario 'phase2_short' result: {'PASS' if success_short else 'FAIL'}")

if not (success_all and success_short):
    sys.exit(1)
