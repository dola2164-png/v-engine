import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import jinja2
from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from engine.context_store import store
from engine.decision_engine import decision_engine
from engine.composer import composer
from engine.conversation_manager import conversation_manager

app = FastAPI(
    title="Vera AI Marketing Decision Engine",
    description="Vera's AI Decision & Message Composition Engine for magicpin merchants",
    version="1.0.0"
)
START_TIME = time.time()
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
TEMPLATES_DIR = BASE_DIR / "templates"

def load_seed_dataset():
    cat_dir = DATASET_DIR / "categories"
    if cat_dir.exists():
        for f in cat_dir.glob("*.json"):
            try:
                data = json.load(open(f, encoding="utf-8"))
                store.push_context("category", data.get("slug", f.stem), 1, data)
            except Exception as e:
                print("Error loading category:", e)

    for name, scope, key in [
        ("merchants_seed.json", "merchant", "merchant_id"),
        ("customers_seed.json", "customer", "customer_id"),
        ("triggers_seed.json", "trigger", "id")
    ]:
        path = DATASET_DIR / name
        if path.exists():
            try:
                data = json.load(open(path, encoding="utf-8"))
                items = data.get(scope + "s", data.get(scope, []))
                for it in items:
                    if key in it:
                        store.push_context(scope, it[key], 1, it)
            except Exception as e:
                print("Error loading seed:", name, e)

# Initial load
load_seed_dataset()

# --- Models ---
class ContextPayload(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str

class TickPayload(BaseModel):
    now: Optional[str] = None
    available_triggers: List[str] = []

class ReplyPayload(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: Optional[str] = None
    turn_number: int = 1

# --- Interactive Web Dashboard ---
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    counts = store.get_counts()
    if counts.get("trigger", 0) == 0:
        load_seed_dataset()
        counts = store.get_counts()

    merchants = store.get_all_by_scope("merchant")
    triggers = store.get_all_by_scope("trigger")
    categories = store.get_all_by_scope("category")

    template_file = TEMPLATES_DIR / "index.html"
    if template_file.exists():
        template_str = open(template_file, encoding="utf-8").read()
        tmpl = jinja2.Template(template_str)
        html = tmpl.render(
            counts=counts,
            triggers=triggers,
            categories=categories,
            merchants=merchants
        )
        return HTMLResponse(content=html)
    
    return HTMLResponse(content="<h1>Dashboard Template Not Found</h1>", status_code=500)

# --- API Endpoints ---

@app.get("/v1/healthz")
async def healthz():
    counts = store.get_counts()
    uptime = int(time.time() - START_TIME)
    return {
        "status": "ok",
        "uptime_seconds": uptime,
        "contexts_loaded": counts
    }

@app.get("/v1/metadata")
async def metadata():
    return {
        "team_name": "Vera Elite",
        "team_members": ["Agentic AI Engineer"],
        "model": "deterministic-decision-engine+llm",
        "approach": "4-context signal extraction, suppression ranking, category-specific reasoning and zero-hallucination validation",
        "contact_email": "vera.engine@magicpin.in",
        "version": "1.0.0",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

@app.post("/v1/context")
async def push_context(body: ContextPayload, response: Response):
    accepted, result, cur_v = store.push_context(
        scope=body.scope,
        context_id=body.context_id,
        version=body.version,
        payload=body.payload
    )

    if not accepted:
        response.status_code = status.HTTP_409_CONFLICT
        return {
            "accepted": False,
            "reason": result,
            "current_version": cur_v
        }

    return {
        "accepted": True,
        "ack_id": result,
        "stored_at": datetime.now(timezone.utc).isoformat()
    }

@app.post("/v1/tick")
async def tick(body: TickPayload):
    triggers_to_process = decision_engine.evaluate_triggers(
        available_trigger_ids=body.available_triggers,
        now_str=body.now
    )

    actions = []
    for trg in triggers_to_process:
        mid = trg.get("merchant_id")
        cid = trg.get("customer_id")

        merchant = store.get_context("merchant", mid) if mid else None
        if not merchant:
            all_merchants = store.get_all_by_scope("merchant")
            for m_id, m_data in all_merchants.items():
                if mid and (mid in m_id or m_id in mid):
                    merchant = m_data
                    break
        
        if not merchant:
            continue

        cat_slug = merchant.get("category_slug", "")
        category = store.get_context("category", cat_slug)
        if not category:
            continue

        customer = store.get_context("customer", cid) if cid else None

        action = composer.compose(
            category=category,
            merchant=merchant,
            trigger=trg,
            customer=customer
        )
        actions.append(action)

        supp_key = action.get("suppression_key")
        if supp_key:
            store.add_suppression(supp_key, trg.get("expires_at"))

    return {"actions": actions}

@app.post("/v1/reply")
async def reply(body: ReplyPayload):
    result = conversation_manager.handle_reply(
        conversation_id=body.conversation_id,
        merchant_id=body.merchant_id,
        customer_id=body.customer_id,
        from_role=body.from_role,
        message=body.message,
        turn_number=body.turn_number
    )
    return result

@app.post("/v1/teardown")
async def teardown():
    store.teardown()
    load_seed_dataset()
    return {"status": "reset_completed"}
