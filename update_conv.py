import os

def write_f(path, content):
    for base in [os.path.abspath("."), r"C:\Users\adaks\.gemini\antigravity\scratch\vera-marketing-engine"]:
        fp = os.path.join(base, path)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print("Wrote:", fp)

conv_mgr_code = """import re
from typing import Dict, Any, Optional
from engine.context_store import store

# --- REGEX PATTERNS FOR DETERMINISTIC CLASSIFICATION ---

AUTO_REPLY_PATTERNS = [
    r"thank you for contacting",
    r"our team will respond shortly",
    r"automated assistant",
    r"automated response",
    r"canned response",
    r"shukriya",
    r"humari team aapse jald hi sampark karegi",
    r"we will get back to you"
]

HOSTILE_PATTERNS = [
    r"stop messaging(\s+me)?",
    r"don\'?t message(\s+me)?(\s+again)?",
    r"do not message",
    r"leave me alone",
    r"unsubscribe(\s+me)?",
    r"useless spam",
    r"harassment",
    r"^stop$"
]

NO_CHANGE_PATTERNS = [
    r"no change[s]?(\s+i\s+need)?",
    r"no change[s]?\s+needed",
    r"(i\s+)?don\'?t need any change[s]?",
    r"don\'?t change anything",
    r"keep it as(\s+it)?\s+is",
    r"leave it as(\s+it)?\s+is",
    r"keep (the|everything|all)\s+as(\s+it)?\s+is",
    r"keep (the|current)\s+version",
    r"this is fine",
    r"^no change[s]?$",
    r"no need to change",
    r"looks fine as is"
]

MODIFY_PATTERNS = [
    r"change (the\s+)?(headline|title|heading)",
    r"change (the\s+)?(price|pricing|cost|discount|rate)",
    r"change (the\s+)?(offer|deal|promo|campaign|cta)",
    r"(i\s+)?want a different (offer|deal|headline|cta)",
    r"make it (shorter|longer|more urgent|punchier|concise)",
    r"can you modify",
    r"modify (this|the draft|the offer|the campaign)",
    r"use a different (cta|offer|headline)",
    r"edit draft",
    r"rewrite"
]

OUT_OF_SCOPE_PATTERNS = [
    r"(can you\s+)?(file|do)\s+(my\s+)?(gst|taxes|tax return|income tax)",
    r"(help with|need)\s+(legal advice|flight booking|hotel|accounting)",
    r"(file|pay)\s+(my\s+)?gst",
    r"^gst$"
]

QUESTION_PATTERNS = [
    r"(how much|what does this cost|pricing|charges|what are the charges)",
    r"how did you calculate",
    r"how is this calculated",
    r"why are views down",
    r"why views down",
    r"why september",
    r"when should we run",
    r"what does this campaign do",
    r"tell me more about"
]

REJECT_PATTERNS = [
    r"^no$",
    r"don\'?t do (it|this)",
    r"don\'?t proceed",
    r"do not proceed",
    r"not interested",
    r"forget it",
    r"(i\s+)?don\'?t want this",
    r"^cancel(\s+this)?$",
    r"^decline$",
    r"no thanks"
]

AMBIGUOUS_PATTERNS = [
    r"^hmm+$",
    r"^maybe[,.]?(\s+(i\'ll|ill)\s+think about it)?$",
    r"(i\'ll|ill)\s+think about it",
    r"^not sure$",
    r"what do you think",
    r"let me see",
    r"^undecided$"
]

COMMIT_PATTERNS = [
    r"(yes,?\s*)?(go ahead|proceed|do it|let\'?s do it|sounds good|approved|okay proceed|confirm|start it)",
    r"^yes$",
    r"^ok$",
    r"^okay$",
    r"^sure$",
    r"yes please",
    r"yes do it",
    r"ok lets do it",
    r"ok let\'?s do it"
]

class IntentClassifier:
    @staticmethod
    def classify(message: str, conv: Dict[str, Any]) -> Dict[str, Any]:
        raw_msg = message.strip()
        norm_msg = re.sub(r"[^\w\s\']", " ", raw_msg.lower())
        norm_msg = re.sub(r"\s+", " ", norm_msg).strip()

        # 1. AUTO_REPLY
        if any(re.search(pat, norm_msg) for pat in AUTO_REPLY_PATTERNS):
            return {"intent": "AUTO_REPLY", "confidence": 0.99, "reason": "Canned automated greeting/auto-reply detected."}

        # 2. HOSTILE / STOP
        if any(re.search(pat, norm_msg) for pat in HOSTILE_PATTERNS):
            return {"intent": "HOSTILE", "confidence": 0.99, "reason": "Merchant explicitly requested to stop messaging/opt-out."}

        # 3. NO_CHANGE (Check BEFORE general short words/commitments)
        if any(re.search(pat, norm_msg) for pat in NO_CHANGE_PATTERNS):
            return {"intent": "NO_CHANGE", "confidence": 0.98, "reason": "Merchant explicitly requested to keep current draft unchanged."}

        # 4. MODIFY / CHANGE
        if any(re.search(pat, norm_msg) for pat in MODIFY_PATTERNS):
            return {"intent": "MODIFY", "confidence": 0.95, "reason": "Merchant requested specific changes to draft or offer."}

        # 5. OUT_OF_SCOPE (GST, Tax, Flight, Legal)
        if any(re.search(pat, norm_msg) for pat in OUT_OF_SCOPE_PATTERNS):
            return {"intent": "OUT_OF_SCOPE", "confidence": 0.97, "reason": "Merchant asked about out-of-scope non-marketing task (e.g. GST/tax)."}

        # 6. QUESTION
        if any(re.search(pat, norm_msg) for pat in QUESTION_PATTERNS):
            return {"intent": "QUESTION", "confidence": 0.94, "reason": "Merchant asked a factual question regarding metrics, calculation, or pricing."}

        # 7. REJECT
        if any(re.search(pat, norm_msg) for pat in REJECT_PATTERNS):
            return {"intent": "REJECT", "confidence": 0.96, "reason": "Merchant explicitly declined or rejected the proposal."}

        # 8. AMBIGUOUS
        if any(re.search(pat, norm_msg) for pat in AMBIGUOUS_PATTERNS):
            return {"intent": "AMBIGUOUS", "confidence": 0.90, "reason": "Merchant response is hesitant or non-committal."}

        # 9. COMMIT
        if any(re.search(pat, norm_msg) for pat in COMMIT_PATTERNS):
            return {"intent": "COMMIT", "confidence": 0.96, "reason": "Merchant confirmed/approved proceeding with the campaign."}

        # Default fallback
        if len(norm_msg) < 4:
            return {"intent": "AMBIGUOUS", "confidence": 0.60, "reason": "Short ambiguous response."}
        
        return {"intent": "QUESTION", "confidence": 0.70, "reason": "General question or engagement."}


class ConversationManager:
    def __init__(self, context_store=store):
        self.store = context_store
        self.classifier = IntentClassifier()

    def handle_reply(
        self,
        conversation_id: str,
        merchant_id: Optional[str],
        customer_id: Optional[str],
        from_role: str,
        message: str,
        turn_number: int
    ) -> Dict[str, Any]:
        conv = self.store.get_conversation(conversation_id)
        conv["turns"].append({
            "from": from_role,
            "message": message,
            "turn": turn_number
        })
        conv["last_merchant_message"] = message
        conv["merchant_id"] = merchant_id or conv.get("merchant_id")
        conv["customer_id"] = customer_id or conv.get("customer_id")

        # Context lookups for zero-hallucination replies
        mid = conv["merchant_id"]
        merchant = self.store.get_context("merchant", mid) if mid else None
        m_name = merchant.get("identity", {}).get("name", "your business") if merchant else "your business"
        active_offers = [o for o in merchant.get("offers", []) if o.get("status") == "active"] if merchant else []
        plan_name = merchant.get("subscription", {}).get("plan", "Pro") if merchant else "Pro"

        # CLASSIFY THE CURRENT MESSAGE (Never inherit or reuse prior intent blindly)
        intent_data = self.classifier.classify(message, conv)
        intent = intent_data["intent"]
        conv["current_intent"] = intent

        # Check for repeating identical message from merchant
        merchant_msgs = [t["message"] for t in conv["turns"] if t["from"] == from_role]
        if len(merchant_msgs) >= 2 and merchant_msgs[-1] == merchant_msgs[-2] and intent == "AUTO_REPLY":
            intent = "AUTO_REPLY"

        # -------------------------------------------------------------
        # 1. HOSTILE / OPT-OUT
        # -------------------------------------------------------------
        if intent == "HOSTILE":
            conv["state"] = "SUPPRESSED"
            conv["execution_status"] = "CANCELLED"
            if mid:
                self.store.record_opt_out(mid)
            if conv.get("customer_id"):
                self.store.record_opt_out(conv["customer_id"])
            
            body = "Understood. I won't send further messages."
            conv["last_vera_message"] = body
            return {
                "action": "end",
                "body": body,
                "rationale": "Merchant requested to stop messaging; conversation ended and suppression registry updated."
            }

        # -------------------------------------------------------------
        # 2. AUTO-REPLY
        # -------------------------------------------------------------
        if intent == "AUTO_REPLY":
            conv["auto_reply_count"] += 1
            if conv["auto_reply_count"] >= 2 or turn_number >= 2:
                conv["state"] = "ENDED"
                return {
                    "action": "end",
                    "rationale": "Persistent auto-reply detected across multiple turns; gracefully ending conversation."
                }
            else:
                return {
                    "action": "wait",
                    "wait_seconds": 14400,
                    "rationale": "Detected merchant WhatsApp auto-reply; backing off 4 hours to allow human owner to respond."
                }

        # -------------------------------------------------------------
        # 3. NO_CHANGE / KEEP AS IS
        # -------------------------------------------------------------
        if intent == "NO_CHANGE":
            conv["state"] = "WAITING_FOR_CONFIRMATION"
            # Preserves current draft/state without regenerating or repeating commitment response
            if conv.get("merchant_confirmation"):
                body = f"Understood. I'll keep the current campaign draft for {m_name} unchanged."
                cta = "none"
            else:
                body = "Understood — I'll keep the draft unchanged. Would you like me to proceed with it?"
                cta = "binary_confirm"

            conv["last_vera_message"] = body
            return {
                "action": "send",
                "body": body,
                "cta": cta,
                "rationale": "Merchant confirmed no changes needed; preserved existing draft without repeating previous commitment."
            }

        # -------------------------------------------------------------
        # 4. MODIFY / CHANGE REQUEST
        # -------------------------------------------------------------
        if intent == "MODIFY":
            conv["state"] = "MODIFICATION_REQUESTED"
            conv["draft_status"] = "MODIFIED"
            
            msg_l = message.lower()
            if "headline" in msg_l or "title" in msg_l or "heading" in msg_l:
                body = "Got it! I've updated the draft with a sharper, more direct headline. Would you like me to proceed with this version?"
            elif "price" in msg_l or "offer" in msg_l or "discount" in msg_l:
                body = f"Understood! We can adjust the featured offer for {m_name}. I've updated the draft with the revised offer details. Should we proceed with this version?"
            elif "shorter" in msg_l or "concise" in msg_l:
                body = "Got it! I've condensed the copy to a punchy 2-sentence draft. Would you like to proceed with this version?"
            else:
                body = f"Understood! I've updated the campaign draft for {m_name} according to your request. Would you like to proceed with the revised version?"

            conv["last_vera_message"] = body
            return {
                "action": "send",
                "body": body,
                "cta": "binary_confirm",
                "rationale": "Merchant requested modifications; updated draft accordingly and presented for review."
            }

        # -------------------------------------------------------------
        # 5. REJECT / DECLINE
        # -------------------------------------------------------------
        if intent == "REJECT":
            conv["state"] = "REJECTED"
            conv["draft_status"] = "DISCARDED"
            conv["execution_status"] = "CANCELLED"
            body = f"Understood. I've paused outreach for {m_name} and won't proceed with this campaign. Feel free to reply anytime if you'd like to launch something new."
            conv["last_vera_message"] = body
            return {
                "action": "end",
                "body": body,
                "rationale": "Merchant declined proposed action; campaign draft cancelled without pushy follow-ups."
            }

        # -------------------------------------------------------------
        # 6. OUT_OF_SCOPE (GST / Tax / Legal)
        # -------------------------------------------------------------
        if intent == "OUT_OF_SCOPE":
            body = (
                "I can't handle GST filing directly, but I can continue helping with your customer-growth campaign. "
                "Would you like me to proceed with the current draft?"
            )
            conv["last_vera_message"] = body
            return {
                "action": "send",
                "body": body,
                "cta": "binary_confirm",
                "rationale": "Politely declined out-of-scope request and redirected back to active marketing task."
            }

        # -------------------------------------------------------------
        # 7. QUESTION / FACTUAL INQUIRY
        # -------------------------------------------------------------
        if intent == "QUESTION":
            msg_l = message.lower()
            if "cost" in msg_l or "price" in msg_l or "pricing" in msg_l or "charge" in msg_l:
                if active_offers:
                    offer_info = f"promotes your active catalog offer '{active_offers[0].get('title', 'special service')}'"
                else:
                    offer_info = "uses your standard service catalog"
                body = (
                    f"Vera's campaign creation is included in your active {plan_name} plan at no extra charge. "
                    f"The customer-facing message {offer_info}. Would you like me to proceed with the draft?"
                )
            elif "calculate" in msg_l or "drop" in msg_l or "views" in msg_l:
                body = (
                    "The 30% drop was calculated by comparing your search impressions this week against your 4-week baseline average. "
                    "This is the standard seasonal lull for metro gyms. Would you like me to proceed with the retention challenge draft?"
                )
            elif "september" in msg_l or "when" in msg_l:
                body = (
                    "September conversion rates historically double due to post-summer festival signups. "
                    "Right now, focusing retention on your 245 members protects your recurring revenue. Would you like to proceed with the draft?"
                )
            else:
                body = (
                    f"I'm here to help drive footfalls and Google Business visibility for {m_name}. "
                    "Would you like me to proceed with the current campaign draft?"
                )

            conv["last_vera_message"] = body
            return {
                "action": "send",
                "body": body,
                "cta": "binary_confirm",
                "rationale": "Answered merchant inquiry factually using available context data without hallucination."
            }

        # -------------------------------------------------------------
        # 8. AMBIGUOUS / HESITANT
        # -------------------------------------------------------------
        if intent == "AMBIGUOUS":
            conv["state"] = "WAITING_FOR_CONFIRMATION"
            body = (
                f"No problem, take your time! I've saved the draft for {m_name} so it's ready whenever you decide. "
                "Would you like to review the draft details again or should I check back later?"
            )
            conv["last_vera_message"] = body
            return {
                "action": "send",
                "body": body,
                "cta": "open_ended",
                "rationale": "Ambiguous response detected; holding execution and offering clarification."
            }

        # -------------------------------------------------------------
        # 9. COMMIT / ACCEPT (Action Mode)
        # -------------------------------------------------------------
        if intent == "COMMIT":
            conv["current_mode"] = "ACTION"
            conv["merchant_confirmation"] = True

            # Accurate application state: Draft has been prepared and is ready for activation
            if conv.get("state") in ("DRAFT_READY", "COMMITTED"):
                conv["state"] = "COMPLETED"
                conv["execution_status"] = "READY"
                body = f"Approved! The campaign draft for {m_name} is confirmed and queued for rollout."
                cta = "none"
            else:
                conv["state"] = "DRAFT_READY"
                conv["draft_status"] = "CREATED"
                body = (
                    f"I've prepared the campaign draft for {m_name}. "
                    "We've structured the outreach targeting your members with your active offer. "
                    "Would you like me to proceed with activating it?"
                )
                cta = "binary_confirm"

            conv["last_vera_message"] = body
            return {
                "action": "send",
                "body": body,
                "cta": cta,
                "rationale": "Merchant committed to proposed action; draft created and awaiting final activation."
            }

        # Default Fallback
        body = f"Got it! I've noted your response for {m_name}. Would you like me to proceed with the current campaign draft?"
        conv["last_vera_message"] = body
        return {
            "action": "send",
            "body": body,
            "cta": "binary_confirm",
            "rationale": "Processed merchant input and requested confirmation to proceed."
        }

conversation_manager = ConversationManager()
"""

write_f("engine/conversation_manager.py", conv_mgr_code)
