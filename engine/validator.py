from typing import Dict, Any, List
from engine.category_rules import get_taboos

class MessageValidator:
    def __init__(self):
        pass

    def validate_message(self, cat_slug: str, body: str) -> Dict[str, Any]:
        taboos = get_taboos(cat_slug)
        body_lower = body.lower()
        found_taboos = [t for t in taboos if t.lower() in body_lower]
        has_taboo = len(found_taboos) > 0
        has_cta = any(w in body_lower for w in ["reply", "want me", "call", "slots", "?"])
        return {
            "valid": not has_taboo,
            "has_taboo": has_taboo,
            "found_taboos": found_taboos,
            "has_cta": has_cta
        }

validator = MessageValidator()
