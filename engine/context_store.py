import threading
from datetime import datetime, timezone
from typing import Dict, Tuple, Any, Optional

class ContextStore:
    def __init__(self):
        self._lock = threading.RLock()
        self._contexts: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._suppressions: Dict[str, str] = {}
        self._conversations: Dict[str, Dict[str, Any]] = {}
        self._opt_outs: set = set()

    def push_context(self, scope: str, context_id: str, version: int, payload: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        with self._lock:
            key = (scope, context_id)
            existing = self._contexts.get(key)
            if existing is not None:
                cur_v = existing.get("version", 0)
                if cur_v > version:
                    return False, "stale_version", cur_v
                elif cur_v == version:
                    if scope in ("merchant", "customer"):
                        self._opt_outs.discard(context_id)
                    return True, f"ack_{context_id}_v{version}", None

            self._contexts[key] = {
                "version": version,
                "payload": payload,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if scope in ("merchant", "customer"):
                self._opt_outs.discard(context_id)
                
            ack_id = f"ack_{context_id}_v{version}"
            return True, ack_id, None

    def get_context(self, scope: str, context_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            item = self._contexts.get((scope, context_id))
            return item["payload"] if item else None

    def get_all_by_scope(self, scope: str) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {
                cid: item["payload"]
                for (sc, cid), item in self._contexts.items()
                if sc == scope
            }

    def get_counts(self) -> Dict[str, int]:
        with self._lock:
            counts = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
            for (scope, _), _ in self._contexts.items():
                counts[scope] = counts.get(scope, 0) + 1
            return counts

    def is_suppressed(self, suppression_key: Optional[str]) -> bool:
        if not suppression_key:
            return False
        with self._lock:
            return suppression_key in self._suppressions

    def add_suppression(self, suppression_key: Optional[str], expires_at: Optional[str] = None):
        if not suppression_key:
            return
        with self._lock:
            self._suppressions[suppression_key] = expires_at or datetime.now(timezone.utc).isoformat()

    def record_opt_out(self, target_id: str):
        with self._lock:
            self._opt_outs.add(target_id)

    def is_opted_out(self, target_id: Optional[str]) -> bool:
        if not target_id:
            return False
        with self._lock:
            return target_id in self._opt_outs

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        with self._lock:
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = {
                    "conversation_id": conversation_id,
                    "turns": [],
                    "state": "PROPOSED",
                    "current_intent": None,
                    "current_mode": "INITIAL",
                    "last_vera_message": None,
                    "last_merchant_message": None,
                    "current_proposal": None,
                    "draft_status": "NONE",
                    "execution_status": "PENDING",
                    "merchant_confirmation": False,
                    "auto_reply_count": 0,
                    "merchant_id": None,
                    "customer_id": None,
                    "trigger_id": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            return self._conversations[conversation_id]

    def update_conversation(self, conversation_id: str, **kwargs):
        with self._lock:
            conv = self.get_conversation(conversation_id)
            conv.update(kwargs)
            conv["updated_at"] = datetime.now(timezone.utc).isoformat()

    def teardown(self):
        with self._lock:
            self._contexts.clear()
            self._suppressions.clear()
            self._conversations.clear()
            self._opt_outs.clear()

store = ContextStore()
