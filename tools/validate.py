#!/usr/bin/env python3
"""MS Ads Sponsored Answer Spec v0.1 (draft) validator.

Usage:
  python3 validate.py request  FILE
  python3 validate.py response FILE [--request REQFILE]   # pair checks
  python3 validate.py event    FILE
Exit code 0 = valid, 1 = invalid. Prints the errors.
JSON Schema checks + semantic rules the schema can't express (PII, claims, pairing, no-bid rules).
"""
import json, re, sys, pathlib
from jsonschema import Draft202012Validator, FormatChecker

HERE = pathlib.Path(__file__).resolve().parent.parent
SCHEMAS = {k: json.loads((HERE / f"schema/sa-{n}.schema.json").read_text())
           for k, n in [("request", "bid-request"), ("response", "bid-response"), ("event", "event")]}

PII = [
    (re.compile(r"(\+92|0)3\d{2}[- ]?\d{7}"), "PK mobile number"),
    (re.compile(r"\+?\d[\d -]{9,}\d"), "phone-like number"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email address"),
    (re.compile(r"\b\d{5}-\d{7}-\d\b"), "CNIC"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "card/account number"),
]
CLAIMS = re.compile(r"(world'?s\s*(#?1|first|best|only)|first in the world|duniya (ka|mein) (pehla|sab se)|#1\b|guaranteed best|100% guaranteed)", re.I)
LABELS_OK = {"Sponsored", "Ad", "Sponsored (ishtehar)", "اشتہار", "Ishtehar", "Sponsorlu", "إعلان", "विज्ञापन"}


def schema_errors(kind, doc):
    v = Draft202012Validator(SCHEMAS[kind], format_checker=FormatChecker())
    return [f"schema: /{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in sorted(v.iter_errors(doc), key=str)]


def pii_hits(text):
    return [name for rx, name in PII if text and rx.search(text)]


def semantic_request(doc):
    errs, notes = [], []
    ag = doc.get("ext", {}).get("agent", {})
    conv = ag.get("conversation", {})
    for field in [conv.get("summary", "")] + conv.get("topic", {}).get("keywords", []):
        for h in pii_hits(field):
            errs.append(f"privacy: {h} found in conversation text ({field[:40]!r}); send intent only, no PII")
    c = ag.get("consent", {})
    if c and (not c.get("ads", False) or c.get("age_gate") == "minor" or conv.get("sensitive")):
        notes.append("no-bid required: consent.ads=false, minor, or sensitive conversation")
    if doc.get("at") == 2:
        notes.append("at=2 (second price): v0.1 recommends at=1 (first price)")
    return errs, notes


def semantic_response(doc, req=None):
    errs = []
    slots = {}
    if req:
        for imp in req.get("imp", []):
            slots[imp["id"]] = imp.get("ext", {}).get("sa", {})
        r_notes = semantic_request(req)[1]
        if any(n.startswith("no-bid") for n in r_notes) and doc.get("seatbid"):
            errs.append("policy: request requires no-bid but response has bids")
    for sb in doc.get("seatbid", []):
        for b in sb.get("bid", []):
            sa = b.get("ext", {}).get("sa", {})
            ans = sa.get("answer", {})
            txt = " ".join([ans.get("title", ""), ans.get("text", "")])
            if CLAIMS.search(txt):
                errs.append(f"claims: unverifiable superlative in bid {b.get('id')} ({CLAIMS.search(txt).group(0)!r})")
            for h in pii_hits(ans.get("text", "")):
                errs.append(f"privacy: {h} in sponsored text of bid {b.get('id')}")
            d = sa.get("disclosure", {})
            if d and d.get("sponsor") and d["sponsor"].lower() not in txt.lower() and not ans.get("title"):
                errs.append(f"disclosure: sponsor name not visible in bid {b.get('id')}")
            slot = slots.get(b.get("impid"))
            if req and slot is None:
                errs.append(f"pair: bid {b.get('id')} impid {b.get('impid')} not in request")
            elif slot:
                if sa.get("format") not in slot.get("formats", []):
                    errs.append(f"pair: format {sa.get('format')!r} not allowed by imp {b['impid']} {slot.get('formats')}")
                if slot.get("pricing") and sa.get("pricing") not in slot["pricing"]:
                    errs.append(f"pair: pricing {sa.get('pricing')!r} not accepted")
                mx = slot.get("max_text_chars")
                if mx and len(ans.get("text", "")) > mx:
                    errs.append(f"pair: text {len(ans['text'])} chars > max_text_chars {mx}")
                if slot.get("lite") and ans.get("image", {}).get("bytes", 0) > 30720:
                    errs.append("pair: lite slot but image > 30 KB")
                imp = next(i for i in req["imp"] if i["id"] == b["impid"])
                if b.get("price", 0) < imp.get("bidfloor", 0):
                    errs.append(f"pair: price {b['price']} below bidfloor {imp['bidfloor']}")
                rl = req["ext"]["agent"]["conversation"]["lang"].get("reply_lang")
                if rl and ans.get("lang") and ans["lang"].split("-")[0] != rl.split("-")[0]:
                    errs.append(f"pair: answer lang {ans['lang']} != reply_lang {rl}")
    return errs


def validate(kind, doc, req=None):
    errs = schema_errors(kind, doc)
    notes = []
    if kind == "request":
        e, notes = semantic_request(doc); errs += e
    elif kind == "response":
        errs += semantic_response(doc, req)
    return errs, notes


def main(argv):
    if len(argv) < 3 or argv[1] not in SCHEMAS:
        print(__doc__); return 2
    kind, path = argv[1], argv[2]
    req = json.loads(pathlib.Path(argv[argv.index("--request") + 1]).read_text()) if "--request" in argv else None
    errs, notes = validate(kind, json.loads(pathlib.Path(path).read_text()), req)
    for n in notes: print("note:", n)
    for e in errs: print("ERROR", e)
    print("VALID" if not errs else f"INVALID ({len(errs)} error(s))")
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
