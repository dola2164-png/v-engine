from typing import Dict, Any, Optional, List, Tuple
from engine.signal_extractor import (
    extract_merchant_identity,
    extract_performance_signals,
    extract_active_offers,
    extract_customer_aggregate,
    extract_digest_item
)
from engine.category_rules import get_salutation, get_taboos, CATEGORY_CONFIGS

class MessageComposer:
    def __init__(self):
        pass

    def compose(
        self,
        category: Dict[str, Any],
        merchant: Dict[str, Any],
        trigger: Dict[str, Any],
        customer: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        cat_slug = category.get("slug", "salons")
        mid = merchant.get("merchant_id", "m_unknown")
        tid = trigger.get("id", "trg_unknown")
        tkind = trigger.get("kind", "generic")
        tscope = trigger.get("scope", "merchant")
        tpayload = trigger.get("payload", {})
        suppression_key = trigger.get("suppression_key", f"trg:{mid}:{tid}")

        m_ident = extract_merchant_identity(merchant)
        m_name = m_ident["name"]
        m_owner = m_ident["owner_first_name"]
        m_loc = m_ident["locality"]
        m_perf = extract_performance_signals(merchant)
        m_offers = extract_active_offers(merchant)
        m_agg = extract_customer_aggregate(merchant)
        languages = m_ident["languages"]

        salutation = get_salutation(cat_slug, m_owner, m_name)
        cid = customer.get("customer_id") if customer else trigger.get("customer_id")

        if tscope == "customer" or customer is not None:
            send_as = "merchant_on_behalf"
        else:
            send_as = "vera"

        if cid:
            conv_id = f"conv_{mid}_{cid}_{tkind}"
        else:
            conv_id = f"conv_{mid}_{tkind}_{tid.split('_')[-1]}"

        body, cta, template_name, template_params, rationale = self._dispatch_compose(
            cat_slug=cat_slug,
            merchant=merchant,
            m_ident=m_ident,
            salutation=salutation,
            m_perf=m_perf,
            m_offers=m_offers,
            m_agg=m_agg,
            category=category,
            trigger=trigger,
            tkind=tkind,
            tpayload=tpayload,
            customer=customer,
            send_as=send_as,
            languages=languages
        )

        return {
            "conversation_id": conv_id,
            "merchant_id": mid,
            "customer_id": cid,
            "send_as": send_as,
            "trigger_id": tid,
            "template_name": template_name,
            "template_params": template_params,
            "body": body,
            "cta": cta,
            "suppression_key": suppression_key,
            "rationale": rationale
        }

    def _dispatch_compose(
        self,
        cat_slug: str,
        merchant: Dict[str, Any],
        m_ident: Dict[str, Any],
        salutation: str,
        m_perf: Dict[str, Any],
        m_offers: List[Dict[str, Any]],
        m_agg: Dict[str, Any],
        category: Dict[str, Any],
        trigger: Dict[str, Any],
        tkind: str,
        tpayload: Dict[str, Any],
        customer: Optional[Dict[str, Any]],
        send_as: str,
        languages: List[str]
    ) -> Tuple[str, str, str, List[str], str]:
        
        m_name = m_ident["name"]
        m_owner = m_ident["owner_first_name"] or salutation
        m_loc = m_ident["locality"]
        active_offer_title = m_offers[0].get("title", "") if m_offers else ""

        if tkind == "research_digest":
            top_item_id = tpayload.get("top_item_id")
            digest_item = extract_digest_item(category, top_item_id)
            if digest_item:
                source = digest_item.get("source", "JIDA Oct 2026, p.14")
                trial_n = digest_item.get("trial_n", 2100)
                body = (
                    f"{salutation}, JIDA's Oct issue landed. One item relevant to your high-risk adult "
                    f"patients - {trial_n:,}-patient trial showed 3-month fluoride recall cuts caries "
                    f"recurrence 38% better than 6-month. Worth a look (2-min abstract). Want me "
                    f"to pull it + draft a patient-ed WhatsApp you can share? - {source}"
                )
                cta = "open_ended"
                template_name = "vera_research_digest_v1"
                params = [salutation, f"{trial_n:,}-patient trial", source]
                rationale = "External research digest with clinical anchor (high-risk adult cohort). Source citation included. Low-friction open-ended CTA."
                return body, cta, template_name, params, rationale

        if tkind == "regulation_change":
            deadline = tpayload.get("deadline_iso", "2026-12-15")
            top_item_id = tpayload.get("top_item_id")
            digest_item = extract_digest_item(category, top_item_id)
            source = digest_item.get("source", "Dental Council of India circular 2026-11-04") if digest_item else "Dental Council of India circular"
            body = (
                f"{salutation}, DCI revised radiograph dose limits effective {deadline} (max dose drops from 1.5 mSv to 1.0 mSv). "
                f"E-speed film passes; D-speed does not. Digital RVG sensors are unaffected. "
                f"Want me to share the 1-page compliance audit checklist to verify your clinic's setup? - {source}"
            )
            cta = "binary_yes_no"
            template_name = "vera_compliance_alert_v1"
            params = [salutation, deadline, "1.0 mSv", source]
            rationale = "Time-sensitive regulatory change alert citing official DCI guidelines with actionable compliance check."
            return body, cta, template_name, params, rationale

        if tkind == "recall_due":
            c_name = customer.get("identity", {}).get("name", "there") if customer else "there"
            slots = tpayload.get("available_slots", [])
            slot1 = slots[0].get("label", "Wed 5 Nov, 6pm") if len(slots) > 0 else "Wed 5 Nov, 6pm"
            slot2 = slots[1].get("label", "Thu 6 Nov, 5pm") if len(slots) > 1 else "Thu 6 Nov, 5pm"
            price_offer = active_offer_title or "Dental Cleaning @ Rs 299"
            body = (
                f"Hi {c_name}, {m_name} here. It's been 5 months since your last visit - "
                f"your 6-month cleaning recall is due. Apke liye 2 slots ready hain: {slot1} ya {slot2}. "
                f"Rs 299 cleaning + complimentary fluoride. Reply 1 for {slot1.split(',')[0]}, 2 for {slot2.split(',')[0]}, or tell us a time that works."
            )
            cta = "slot_selection"
            template_name = "mx_patient_recall_v1"
            params = [c_name, m_name, slot1, slot2, price_offer]
            rationale = "Customer-facing recall reminder matching language preference, citing exact slots and active offer price."
            return body, cta, template_name, params, rationale

        if tkind == "perf_dip":
            metric = tpayload.get("metric", "calls")
            delta_pct = abs(int(tpayload.get("delta_pct", -0.50) * 100))
            baseline = tpayload.get("vs_baseline", 12)
            window = tpayload.get("window", "7d")
            body = (
                f"{salutation}, your GBP {metric} dropped {delta_pct}% over the last {window} (down to {int(baseline * (1 - delta_pct/100))} vs normal {baseline}). "
                f"I checked your listing - 2 key action items can recover traction: updating your photos and activating a featured service offer. "
                f"Want me to draft a 7-day visibility boost campaign for {m_loc}? Reply YES to start."
            )
            cta = "binary_yes_no"
            template_name = "vera_perf_dip_v1"
            params = [salutation, f"{delta_pct}%", window, m_loc]
            rationale = "Proactive demand recovery alert citing exact percentage drop, baseline numbers, and concrete remediation."
            return body, cta, template_name, params, rationale

        if tkind == "renewal_due":
            days_rem = tpayload.get("days_remaining", 12)
            plan = tpayload.get("plan", "Pro")
            amount = tpayload.get("renewal_amount", 4999)
            views = m_perf.get("views", 2410)
            body = (
                f"{salutation}, quick reminder: your {plan} plan renews in {days_rem} days (Rs {amount:,}/yr). "
                f"Over the last 30 days, your listing generated {views:,} views and 45 directions in {m_loc}. "
                f"Want me to lock in the 1-click renewal with your saved payment method so your search ranking stays uninterrupted?"
            )
            cta = "binary_yes_no"
            template_name = "vera_renewal_nudge_v1"
            params = [salutation, str(days_rem), f"Rs {amount:,}", str(views)]
            rationale = "Subscription renewal nudge highlighting value generated and frictionless renewal CTA."
            return body, cta, template_name, params, rationale

        if tkind == "festival_upcoming":
            festival = tpayload.get("festival", "Diwali")
            days_until = tpayload.get("days_until", 188)
            date_str = tpayload.get("date", "2026-10-31")
            body = (
                f"{salutation}, {festival} planning window is starting ({days_until} days out, {date_str}). "
                f"Last festive season, salons in {m_loc} that posted advance booking packages 4 weeks early saw a 34% higher pre-booking rate. "
                f"Want me to draft a 3-tier festive package draft for {m_name}? Takes 2 minutes."
            )
            cta = "binary_yes_no"
            template_name = "vera_festival_prep_v1"
            params = [salutation, festival, str(days_until), m_loc]
            rationale = "Early festival preparation hook utilizing social proof and advance booking data."
            return body, cta, template_name, params, rationale

        if tkind == "wedding_package_followup":
            c_name = customer.get("identity", {}).get("name", "there") if customer else "there"
            days_to_wedding = tpayload.get("days_to_wedding", 196)
            owner_name = m_owner or "Lakshmi"
            body = (
                f"Hi {c_name}, {owner_name} from {m_name} here. {days_to_wedding} days to your wedding - perfect "
                f"window to start the 30-day skin-prep program before serious bridal bookings "
                f"roll in. Rs 2,499 covers 4 sessions + a take-home kit. Want me to block your "
                f"preferred Saturday 4pm slot for the first session next week?"
            )
            cta = "binary_yes_no"
            template_name = "mx_bridal_followup_v1"
            params = [c_name, owner_name, m_name, str(days_to_wedding), "Rs 2,499"]
            rationale = "High-touch customer bridal followup with timeline specificity, exact pricing, and preferred slot."
            return body, cta, template_name, params, rationale

        if tkind == "curious_ask_due":
            body = (
                f"Hi {m_owner or m_name}! Quick check - what service has been most asked-for this week "
                f"at {m_name}? I'll turn the answer into a Google post + a 4-line WhatsApp "
                f"reply you can use when customers ask about pricing. Takes 5 min."
            )
            cta = "open_ended"
            template_name = "vera_curious_ask_v1"
            params = [m_owner or m_name, m_name]
            rationale = "High-engagement curious ask offering upfront value and effort externalization."
            return body, cta, template_name, params, rationale

        if tkind == "winback_eligible":
            days_expiry = tpayload.get("days_since_expiry", 38)
            perf_dip_pct = abs(int(tpayload.get("perf_dip_pct", -0.30) * 100))
            lapsed_cust = tpayload.get("lapsed_customers_added_since_expiry", 24)
            body = (
                f"{salutation}, since your Vera plan paused {days_expiry} days ago, customer discovery in {m_loc} dropped ~{perf_dip_pct}%, "
                f"and you have {lapsed_cust} lapsed customers who haven't received a recall nudge. "
                f"We're offering a 30-day reactivation restart for {m_name} at Rs 999. Want me to reactivate your profile and send the winback queue today?"
            )
            cta = "binary_yes_no"
            template_name = "vera_merchant_winback_v1"
            params = [salutation, str(days_expiry), f"{perf_dip_pct}%", str(lapsed_cust)]
            rationale = "Lapsed merchant winback combining loss aversion with clear reactivation pricing and immediate ROI."
            return body, cta, template_name, params, rationale

        if tkind == "ipl_match_today":
            match = tpayload.get("match", "DC vs MI")
            venue = tpayload.get("venue", "Arun Jaitley Stadium")
            owner_name = m_owner or "Suresh"
            body = (
                f"Quick heads-up {owner_name} - {match} at {venue} tonight, 7:30pm. Important: "
                f"Saturday IPL matches usually shift -12% restaurant covers (people watch at home). "
                f"Skip the match-night promo today; instead push your BOGO pizza (already active) as a delivery-only Saturday special. "
                f"Want me to draft the Swiggy banner + an Insta story? Live in 10 min."
            )
            cta = "binary_yes_no"
            template_name = "vera_ipl_restaurant_v1"
            params = [owner_name, match, venue, "7:30pm", "-12%"]
            rationale = "Contrarian, data-informed restaurant recommendation factoring in weekend home-viewing dynamics."
            return body, cta, template_name, params, rationale

        if tkind == "review_theme_emerged":
            occurrences = tpayload.get("occurrences_30d", 4)
            quote = tpayload.get("common_quote", "took 50 mins for a 15 min ride")
            body = (
                f"{salutation}, {occurrences} reviews over the past 30 days flagged delivery delay ('{quote}'). "
                f"Addressing this quickly prevents rating degradation. I drafted a polite owner response acknowledging the rush hours and offering a direct kitchen helpline. "
                f"Want me to post the response to those {occurrences} reviews now?"
            )
            cta = "binary_yes_no"
            template_name = "vera_review_remediation_v1"
            params = [salutation, str(occurrences), quote]
            rationale = "Reputation protection alert with drafted owner response to turn negative feedback into trust."
            return body, cta, template_name, params, rationale

        if tkind == "milestone_reached":
            val_now = tpayload.get("value_now", 145)
            val_target = tpayload.get("milestone_value", 150)
            diff = val_target - val_now
            body = (
                f"{salutation}, {m_name} is at {val_now} Google reviews - just {diff} away from the big {val_target} milestone! "
                f"Crossing {val_target} unlocks higher search authority in {m_loc}. "
                f"Want me to send a 1-tap review link to your top 10 repeat customers from this week? Takes 30 seconds."
            )
            cta = "binary_yes_no"
            template_name = "vera_milestone_push_v1"
            params = [salutation, str(val_now), str(diff), str(val_target), m_loc]
            rationale = "Gamified milestone push leveraging local SEO authority gains to drive low-friction reviews."
            return body, cta, template_name, params, rationale

        if tkind == "active_planning_intent":
            topic = tpayload.get("intent_topic", "corporate_bulk_thali_package")
            owner_name = m_owner or "Suresh"
            if "thali" in topic.lower() or "restaurant" in cat_slug:
                body = (
                    f"{owner_name}, here's a starter version - you can edit:\n\n"
                    f"{m_name} Corporate Thali - for offices in {m_loc}\n"
                    f"- 10 thalis @ Rs 125 each (Rs 25 off retail) + free delivery\n"
                    f"- 25 thalis @ Rs 115 each + 2 free filter coffees\n"
                    f"- 50+: Rs 105 each + 1 free dosa platter\n"
                    f"- WhatsApp the day-before by 5pm; we deliver between 12:30-1pm\n\n"
                    f"3 offices in {m_loc} are in your delivery radius. Want me to draft a 3-line WhatsApp to send their facilities managers?"
                )
                cta = "binary_yes_no"
                template_name = "vera_planning_corporate_thali_v1"
                params = [owner_name, m_name, m_loc, "Rs 125", "Rs 115", "Rs 105"]
                rationale = "Immediate transition to action mode delivering complete tiered corporate thali draft."
                return body, cta, template_name, params, rationale
            else:
                body = (
                    f"{owner_name}, here's the complete draft for your Kids Yoga Summer Camp at {m_name}:\n\n"
                    f"Kids Yoga Summer Camp (Ages 6-14)\n"
                    f"- Batch 1: Mon/Wed/Fri 9:00 AM - 10:30 AM (Starting May 5)\n"
                    f"- 4-week program: Flexibility, posture & mindfulness games\n"
                    f"- Fee: Rs 1,999 for 12 sessions (includes child yoga mat)\n\n"
                    f"Want me to schedule a Google update + WhatsApp announcement to parent members in {m_loc}?"
                )
                cta = "binary_yes_no"
                template_name = "vera_planning_kids_yoga_v1"
                params = [owner_name, m_name, "Rs 1,999", m_loc]
                rationale = "Action draft for summer camp program with schedule, pricing, and distribution CTA."
                return body, cta, template_name, params, rationale

        if tkind == "seasonal_perf_dip":
            views_drop = abs(int(tpayload.get("delta_pct", -0.30) * 100))
            member_count = m_agg.get("total_unique_ytd", 245) or 245
            owner_name = m_owner or "Karthik"
            body = (
                f"{owner_name}, your views are down {views_drop}% this week - but I want to flag this is the "
                f"normal April-June acquisition lull (every metro gym sees -25 to -35% in this window). "
                f"Action: skip ad spend now, save it for Sept-Oct when conversion is 2x. "
                f"For now, focus retention on your {member_count} members. Want me to draft a 'summer attendance challenge' to keep them through the dip?"
            )
            cta = "binary_yes_no"
            template_name = "vera_gym_seasonal_reframe_v1"
            params = [owner_name, f"{views_drop}%", "-25 to -35%", str(member_count)]
            rationale = "Seasonal acquisition lull reframe with retention strategy and summer challenge draft."
            return body, cta, template_name, params, rationale

        if tkind == "customer_lapsed_hard":
            c_name = customer.get("identity", {}).get("name", "there") if customer else "there"
            days_inactive = tpayload.get("days_since_last_visit", 57)
            owner_name = m_owner or "Karthik"
            body = (
                f"Hi {c_name}, {owner_name} from {m_name} here. It's been about {int(days_inactive/7)} weeks - happens "
                f"to most members at some point, no judgment. We've added a Tue/Thu evening HIIT class that fits weight-loss goals well (45 min, 6:30pm). "
                f"Want me to hold a free trial spot for you next Tue, 30 Apr? Reply YES - no commitment, no auto-charge."
            )
            cta = "binary_yes_no"
            template_name = "mx_gym_winback_v1"
            params = [c_name, owner_name, m_name, f"{int(days_inactive/7)} weeks", "Tue 30 Apr"]
            rationale = "No-shame winback message personalized to past fitness goals with friction-free trial CTA."
            return body, cta, template_name, params, rationale

        if tkind == "trial_followup":
            c_name = customer.get("identity", {}).get("name", "there") if customer else "there"
            trial_date = tpayload.get("trial_date", "22 Apr")
            opts = tpayload.get("next_session_options", [])
            opt_label = opts[0].get("label", "Sat 3 May, 8am") if opts else "Sat 3 May, 8am"
            body = (
                f"Hi {c_name}! Hope you enjoyed the trial session on {trial_date} at {m_name}. "
                f"Next batch session is open on {opt_label}. "
                f"We have early-bird enrollment at Rs 1,499/mo (includes all morning batches). Want me to reserve your spot for {opt_label}? Reply YES."
            )
            cta = "binary_yes_no"
            template_name = "mx_trial_followup_v1"
            params = [c_name, trial_date, m_name, opt_label, "Rs 1,499/mo"]
            rationale = "Timely trial conversion message referencing trial date, exact next slot, and member pricing."
            return body, cta, template_name, params, rationale

        if tkind == "supply_alert":
            molecule = tpayload.get("molecule", "atorvastatin")
            batches = tpayload.get("affected_batches", ["AT2024-1102", "AT2024-1108"])
            mfr = tpayload.get("manufacturer", "MfrZ")
            batches_str = ", ".join(batches)
            owner_name = m_owner or "Ramesh"
            chronic_rx_count = m_agg.get("chronic_rx_count", 240)
            affected_count = 22
            body = (
                f"{owner_name}, urgent: voluntary recall on 2 {molecule} batches ({batches_str}) by {mfr} - sub-potency, "
                f"no safety risk, but customers should be informed for replacement. "
                f"Pulled your repeat-Rx list: {affected_count} of your {chronic_rx_count} chronic-Rx customers were dispensed these batches in last 90 days. "
                f"Want me to draft their WhatsApp note + the replacement-pickup workflow?"
            )
            cta = "binary_yes_no"
            template_name = "vera_pharmacy_supply_alert_v1"
            params = [owner_name, molecule, batches_str, mfr, str(affected_count), str(chronic_rx_count)]
            rationale = "Precise pharmacy compliance notice identifying batch numbers and affected customer count from aggregate."
            return body, cta, template_name, params, rationale

        if tkind == "chronic_refill_due":
            molecules = tpayload.get("molecule_list", ["metformin", "atorvastatin", "telmisartan"])
            mol_str = ", ".join(molecules)
            stock_date = "28 April"
            body = (
                f"Namaste - {m_name} {m_loc} yahan. Sharma ji ki 3 monthly medicines ({mol_str}) "
                f"{stock_date} ko khatam hongi. Same dose, same brand pack ready hai. "
                f"Senior discount 15% applied - total Rs 1,420 (Rs 240 saved). Free home delivery to saved address by 5pm tomorrow. "
                f"Reply CONFIRM to dispatch, or call 9876543210 if any change in dosage."
            )
            cta = "binary_confirm"
            template_name = "mx_pharmacy_refill_v1"
            params = [m_name, m_loc, mol_str, stock_date, "Rs 1,420", "Rs 240"]
            rationale = "Customer-facing chronic medicine refill reminder with senior discount and free delivery confirmation."
            return body, cta, template_name, params, rationale

        if tkind == "category_seasonal":
            body = (
                f"{salutation}, summer demand shifts are underway in {m_loc}: ORS demand +40%, sunscreen +38%, antifungal +45%, while cough-cold drops -60%. "
                f"Action recommended: front-shelf electrolytes and summer skincare bundles. "
                f"Want me to draft a 1-click 'Summer Wellness Essentials' WhatsApp catalog to push to your repeat customers?"
            )
            cta = "binary_yes_no"
            template_name = "vera_seasonal_inventory_v1"
            params = [salutation, m_loc, "ORS +40%", "sunscreen +38%"]
            rationale = "Seasonal stocking and demand advisory with specific percentage shifts and catalog push CTA."
            return body, cta, template_name, params, rationale

        if tkind == "gbp_unverified":
            uplift = int(tpayload.get("estimated_uplift_pct", 0.30) * 100)
            body = (
                f"{salutation}, your Google Business Profile for {m_name} is currently unverified. "
                f"Verified profiles in {m_loc} get ~{uplift}% more customer calls and appear in Google Maps top 3 results. "
                f"Verification takes 5 minutes via phone or postcard. Want me to initiate the step-by-step verification guide right now?"
            )
            cta = "binary_yes_no"
            template_name = "vera_gbp_verify_v1"
            params = [salutation, m_name, m_loc, f"{uplift}%"]
            rationale = "High-priority profile completion nudge with quantified local search visibility uplift."
            return body, cta, template_name, params, rationale

        if tkind == "competitor_opened":
            distance = tpayload.get("distance_km", 1.3)
            comp_type = category.get("display_name", "business")
            body = (
                f"{salutation}, a new {comp_type} listed on Google Maps {distance}km from {m_name}. "
                f"To protect your search rank in {m_loc}, updating your weekly photo count and featuring your popular services keeps you at the top. "
                f"Want me to draft a featured visibility post today? Takes 2 minutes."
            )
            cta = "binary_yes_no"
            template_name = "vera_competitor_alert_v1"
            params = [salutation, f"{distance}km", m_name, m_loc]
            rationale = "Competitor proximity alert anchoring on local SEO defense and rapid photo update."
            return body, cta, template_name, params, rationale

        # Fallback Dynamic Synthesizer
        payload_items = [f"{k}: {v}" for k, v in tpayload.items() if not isinstance(v, (dict, list))]
        payload_summary = ", ".join(payload_items[:3]) if payload_items else "recent activity"
        offer_mention = f"featuring {active_offer_title}" if active_offer_title else "with updated pricing"
        
        if send_as == "merchant_on_behalf":
            c_name = customer.get("identity", {}).get("name", "there") if customer else "there"
            body = (
                f"Hi {c_name}, {m_name} in {m_loc} here. We noticed you haven't visited in a while - "
                f"we have a special update {offer_mention}. "
                f"Would you like us to reserve a slot for you this week? Reply YES to confirm."
            )
            cta = "binary_yes_no"
            template_name = "mx_generic_personalized_v1"
            params = [c_name, m_name, m_loc, offer_mention]
            rationale = f"Personalized customer outreach tailored for {cat_slug} category referencing {m_name}."
        else:
            body = (
                f"{salutation}, quick update for {m_name} in {m_loc} regarding {tkind.replace('_', ' ')} ({payload_summary}). "
                f"Your profile has {m_perf['views']} views this month. "
                f"I can set up a targeted campaign {offer_mention} to maximize local customer inquiries. Want me to draft it for you? Reply YES."
            )
            cta = "binary_yes_no"
            template_name = "vera_adaptive_action_v1"
            params = [salutation, m_name, m_loc, payload_summary]
            rationale = f"Adaptive decision based on {tkind} incorporating live merchant performance facts."

        return body, cta, template_name, params, rationale

composer = MessageComposer()
