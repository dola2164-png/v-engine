from typing import Dict, Any, Optional, List

def extract_merchant_identity(merchant: Dict[str, Any]) -> Dict[str, Any]:
    identity = merchant.get("identity", {})
    return {
        "name": identity.get("name", "Merchant"),
        "owner_first_name": identity.get("owner_first_name", ""),
        "locality": identity.get("locality", ""),
        "city": identity.get("city", ""),
        "languages": identity.get("languages", ["en"]),
        "verified": identity.get("verified", True)
    }

def extract_performance_signals(merchant: Dict[str, Any]) -> Dict[str, Any]:
    perf = merchant.get("performance", {})
    delta_7d = perf.get("delta_7d", {})
    return {
        "views": perf.get("views", 0),
        "calls": perf.get("calls", 0),
        "directions": perf.get("directions", 0),
        "ctr": perf.get("ctr", 0.0),
        "views_pct_7d": delta_7d.get("views_pct", 0.0),
        "calls_pct_7d": delta_7d.get("calls_pct", 0.0)
    }

def extract_active_offers(merchant: Dict[str, Any]) -> List[Dict[str, Any]]:
    offers = merchant.get("offers", [])
    return [o for o in offers if o.get("status") == "active"]

def extract_customer_aggregate(merchant: Dict[str, Any]) -> Dict[str, Any]:
    agg = merchant.get("customer_aggregate", {})
    return {
        "total_unique_ytd": agg.get("total_unique_ytd", 0),
        "lapsed_180d_plus": agg.get("lapsed_180d_plus", 0),
        "retention_6mo_pct": agg.get("retention_6mo_pct", 0.0),
        "high_risk_adult_count": agg.get("high_risk_adult_count", 0),
        "chronic_rx_count": agg.get("chronic_rx_count", agg.get("total_unique_ytd", 240))
    }

def extract_digest_item(category: Dict[str, Any], item_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not item_id:
        return None
    digest = category.get("digest", [])
    for item in digest:
        if item.get("id") == item_id:
            return item
    return None
