import json, pathlib, sys, unittest
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
import validate as V, msads_compat as C

L = lambda p: json.loads((HERE / p).read_text())
REQ = "examples/valid/request_roman_urdu_purchase.json"


class Valid(unittest.TestCase):
    def test_request(self): self.assertEqual(V.validate("request", L(REQ))[0], [])
    def test_response_paired(self): self.assertEqual(V.validate("response", L("examples/valid/response_card.json"), L(REQ))[0], [])
    def test_events(self):
        for f in ("event_shown", "event_accepted"):
            self.assertEqual(V.validate("event", L(f"examples/valid/{f}.json"))[0], [], f)


class Invalid(unittest.TestCase):
    def check(self, kind, name, needle, paired=False):
        errs = V.validate(kind, L(f"examples/invalid/{name}.json"), L(REQ) if paired else None)[0]
        self.assertTrue(any(needle in e for e in errs), f"{name}: {errs}")
    def test_pii(self): self.check("request", "req_pii_in_summary", "privacy")
    def test_ip(self): self.check("request", "req_device_ip", "/device")
    def test_consent(self): self.check("request", "req_missing_consent", "consent")
    def test_script(self): self.check("request", "req_bad_script", "script")
    def test_no_disclosure(self): self.check("response", "resp_no_disclosure", "disclosure")
    def test_label_after(self): self.check("response", "resp_label_after", "placement")
    def test_format_pair(self): self.check("response", "resp_format_not_allowed_pair", "pair: format", paired=True)
    def test_claims(self): self.check("response", "resp_unverifiable_claim", "claims")


class Rules(unittest.TestCase):
    def test_nobid_when_no_consent(self):
        r = L(REQ); r["ext"]["agent"]["consent"]["ads"] = False
        errs = V.validate("response", L("examples/valid/response_card.json"), r)[0]
        self.assertTrue(any("no-bid" in e for e in errs))
    def test_price_below_floor(self):
        s = L("examples/valid/response_card.json"); s["seatbid"][0]["bid"][0]["price"] = 0.1
        r = L(REQ); r["imp"][0]["bidfloor"] = 0.5
        self.assertTrue(any("bidfloor" in e for e in V.validate("response", s, r)[0]))
    def test_lang_mismatch(self):
        s = L("examples/valid/response_card.json"); s["seatbid"][0]["bid"][0]["ext"]["sa"]["answer"]["lang"] = "ar"
        self.assertTrue(any("reply_lang" in e for e in V.validate("response", s, L(REQ))[0]))


class LiveCompat(unittest.TestCase):
    def test_live_agent_exchange_request_converts_and_validates(self):
        live = L("tests/fixture_live_msads_agent_0.1.json")
        out = C.convert(live)
        errs, _ = V.validate("request", out)
        self.assertEqual(errs, [])
        # backward compatible: old fields kept
        self.assertIn("msads_agent", out["ext"]); self.assertIn("native", out["imp"][0]); self.assertIn("msads_intent", out["imp"][0]["ext"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
