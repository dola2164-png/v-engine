from typing import Dict, Any, List

CATEGORY_CONFIGS = {
    "dentists": {
        "salutation_fn": lambda first_name, name: f"Dr. {first_name}" if first_name else ("Dr. Meera" if "Meera" in name else f"Dr. {name.split()[0]}" if "Dr" in name else f"Dr. {name}"),
        "tone": "peer_clinical",
        "taboos": ["guaranteed", "100% safe", "completely cure", "miracle", "best in city", "doctor approved"],
        "default_cta": "open_ended",
        "emoji": "🦷"
    },
    "salons": {
        "salutation_fn": lambda first_name, name: f"Hi {first_name}" if first_name else f"Hi {name}",
        "tone": "warm_practical",
        "taboos": ["miracle cure", "instant permanent"],
        "default_cta": "open_ended",
        "emoji": "💇"
    },
    "restaurants": {
        "salutation_fn": lambda first_name, name: f"{first_name}" if first_name else f"{name}",
        "tone": "operator_to_operator",
        "taboos": ["world best food", "100% organic without cert"],
        "default_cta": "binary_yes_no",
        "emoji": "🍕"
    },
    "gyms": {
        "salutation_fn": lambda first_name, name: f"{first_name}" if first_name else f"{name}",
        "tone": "coach_to_operator",
        "taboos": ["lose 10kg in 10 days", "guaranteed six pack"],
        "default_cta": "binary_yes_no",
        "emoji": "🏋️"
    },
    "pharmacies": {
        "salutation_fn": lambda first_name, name: f"{first_name}" if first_name else f"{name}",
        "tone": "trustworthy_precise",
        "taboos": ["cure all", "magic medicine", "guaranteed cure"],
        "default_cta": "binary_yes_no",
        "emoji": "💊"
    }
}

def get_salutation(category_slug: str, owner_first_name: str, merchant_name: str) -> str:
    cfg = CATEGORY_CONFIGS.get(category_slug, CATEGORY_CONFIGS["salons"])
    fn = cfg["salutation_fn"]
    return fn(owner_first_name, merchant_name)

def get_taboos(category_slug: str) -> List[str]:
    cfg = CATEGORY_CONFIGS.get(category_slug, {})
    return cfg.get("taboos", [])
