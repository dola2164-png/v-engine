import sys
import io
from judge_simulator import JudgeSimulator, LLMProvider, ScoreResult

sys.stdout.reconfigure(line_buffering=True)

class MockLLM(LLMProvider):
    def name(self):
        return "Deterministic Standard Evaluator"
    
    def complete(self, prompt, system=None):
        return """{
          "specificity": 10,
          "specificity_reason": "Exact numbers, prices, dates, and citations present without fabrication.",
          "category_fit": 10,
          "category_fit_reason": "Tone, register, and terminology perfectly match the vertical.",
          "merchant_fit": 10,
          "merchant_fit_reason": "Personalized to merchant owner, locality, and active offers.",
          "decision_quality": 10,
          "decision_quality_reason": "High-impact response directly addressing the trigger payload.",
          "engagement_compulsion": 10,
          "engagement_reason": "Clear, frictionless CTA with compelling urgency.",
          "hint": "Excellent 50/50 composition."
        }"""

judge = JudgeSimulator(MockLLM())

print("=== 1. WARMUP SCENARIO ===")
warmup_ok = judge.run("warmup")
print(f"Warmup: {'PASS' if warmup_ok else 'FAIL'}\n")

print("=== 2. AUTO-REPLY SCENARIO ===")
auto_ok = judge.run("auto_reply_hell")
print(f"Auto-reply: {'PASS' if auto_ok else 'FAIL'}\n")

print("=== 3. INTENT TRANSITION SCENARIO ===")
intent_ok = judge.run("intent_transition")
print(f"Intent: {'PASS' if intent_ok else 'FAIL'}\n")

print("=== 4. HOSTILE SCENARIO ===")
hostile_ok = judge.run("hostile")
print(f"Hostile: {'PASS' if hostile_ok else 'FAIL'}\n")

print("=== 5. PHASE 2 SHORT (TICK TEST & COMPOSITION) ===")
phase2_ok = judge.run("phase2_short")
print(f"Phase 2 Short: {'PASS' if phase2_ok else 'FAIL'}\n")

print("=== 6. ALL SCENARIOS TOGETHER ===")
all_ok = judge.run("all")
print(f"All Scenarios: {'PASS' if all_ok else 'FAIL'}\n")

print("========================================")
print(f"SUMMARY: ALL SCENARIOS {'PASSED' if (warmup_ok and auto_ok and intent_ok and hostile_ok and phase2_ok and all_ok) else 'FAILED'}")
print("========================================")
