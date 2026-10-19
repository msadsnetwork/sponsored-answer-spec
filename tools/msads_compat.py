#!/usr/bin/env python3
"""Convert a live Agent Exchange buyer request (msads-agent/0.1: imp.native + imp.ext.msads_intent
+ ext.msads_agent) into Sponsored Answer v0.1 WITHOUT removing the old fields, so current DSPs
keep working (additive / backward-compatible). Local tool only.
Usage: python3 msads_compat.py IN.json > OUT.json
"""
import json, sys, copy

TASK2INTENT = {"purchase": "purchase", "book": "book", "compare": "compare", "info": "informational",
               "informational": "informational", "support": "support", "local": "local_find"}
TYPE2TYPE = {"shopping": "shopping_agent", "chat": "chatbot", "assistant": "assistant", "voice": "voice_assistant",
             "search": "search_agent", "task": "task_agent"}


def convert(live):
    out = copy.deepcopy(live)
    ma = live.get("ext", {}).get("msads_agent", {})
    first = live["imp"][0].get("ext", {})
    it, req = first.get("msads_intent", {}), first.get("msads_offer_request", {})
    # privacy: drop identifiers the SA profile forbids
    for k in ("ip", "ipv6", "ifa"):
        out.get("device", {}).pop(k, None)
    out.get("device", {}).get("geo", {}).pop("lat", None); out.get("device", {}).get("geo", {}).pop("lon", None)
    if "user" in out:
        out["user"].pop("id", None); out["user"].pop("buyeruid", None)
    for imp in out["imp"]:
        r = imp.get("ext", {}).get("msads_offer_request", {})
        imp.setdefault("ext", {})["sa"] = {
            "ver": "0.1", "formats": ["card", "text"], "position": "after_answer",
            "max_answers": max(1, min(3, int(r.get("max_offers", 1)))),
            "pricing": [p for p in r.get("pricing_models", ["cpc"]) if p in ("cpm", "cpc", "cpa")] or ["cpc"]}
    lang = it.get("language") or live.get("device", {}).get("language") or "en"
    cat = it.get("category", "uncategorized")
    out.setdefault("ext", {})["agent"] = {
        "ver": "0.1",
        "id": str(ma.get("agent_id", "unknown")),
        "type": TYPE2TYPE.get(ma.get("agent_type", ""), "assistant"),
        "conversation": {
            "intent": TASK2INTENT.get(it.get("task_type", ""), "informational"),
            "topic": {"cattax": 0, "cat": [cat], "keywords": it.get("keywords", [])[:10]},
            "lang": {"code": lang.split("-")[0]},
            "sensitive": False},
        "consent": {"ads": True},
        "disclosure": {"label_supported": True, "separate_ui": True},
    }
    # cattax 0 = 'msads internal category' (mapping to IAB CT 3.0 is a v0.2 TODO)
    return out


if __name__ == "__main__":
    print(json.dumps(convert(json.load(open(sys.argv[1]))), indent=1, ensure_ascii=False))
