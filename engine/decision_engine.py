from typing import Dict, Any, List, Optional
from engine.context_store import store

class DecisionEngine:
    def __init__(self, context_store=store):
        self.store = context_store

    def evaluate_triggers(self, available_trigger_ids: List[str], now_str: Optional[str] = None) -> List[Dict[str, Any]]:
        candidates = []
        for tid in available_trigger_ids:
            trg = self.store.get_context("trigger", tid)
            if not trg:
                continue

            merchant_id = trg.get("merchant_id")
            if merchant_id and self.store.is_opted_out(merchant_id):
                continue

            customer_id = trg.get("customer_id")
            if customer_id and self.store.is_opted_out(customer_id):
                continue

            urgency = trg.get("urgency", 1)
            candidates.append({"trigger": trg, "urgency": urgency})

        # Sort descending by urgency
        candidates.sort(key=lambda c: c["urgency"], reverse=True)
        return [c["trigger"] for c in candidates[:20]]

decision_engine = DecisionEngine()
