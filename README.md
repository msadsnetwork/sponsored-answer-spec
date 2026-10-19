# Sponsored Answer Spec (draft)

**Status:** `v0.1.0-draft`, open for public comment. Fields may change before v1.0.

An open draft extension to **OpenRTB 2.6**, proposed by MS Ads Network, for **labelled sponsored answers** in chatbots, assistants and AI agents. A host describes a conversational moment: intent, decision stage, topic, language and script (including Roman Urdu), consent, and turn context with no personal data. Buyers bid in a normal OpenRTB auction and return a short sponsored answer with mandatory disclosure. Events are `shown`, `clicked` and `accepted`.

## Related work
- [AdCP Sponsored Intelligence](https://docs.adcontextprotocol.org/docs/sponsored-intelligence/product-spectrum) standardizes sponsored responses and brand-agent handoffs at the media-buy and agent-protocol level. This draft is complementary: it carries the slot *inside an OpenRTB bid request*. A mapping is planned for v0.2.
- [IAB Tech Lab Agentic Audiences](https://github.com/InteractiveAdvertisingBureau/openrtb/blob/main/extensions/community_extensions/agentic-audiences.md) embeddings are reused unchanged.
- Details and sources: [spec/RELATED_WORK.md](spec/RELATED_WORK.md).

## Layout
```
spec/SPEC.md            the specification (CC BY 4.0)
spec/RELATED_WORK.md    overlap analysis with sources
schema/*.schema.json    JSON Schema 2020-12: bid request, bid response, event (Apache-2.0)
examples/valid|invalid  example payloads
tools/validate.py       validator: schema + disclosure, privacy and pairing rules
tools/msads_compat.py   adds SA v0.1 fields to an msads-agent/0.1 request (additive)
tests/test_spec.py      unit tests
demo/index.html         static demo page
```

## Quick start
```bash
python3 -m venv .venv && .venv/bin/pip install jsonschema
.venv/bin/python tools/validate.py request examples/valid/request_roman_urdu_purchase.json
.venv/bin/python tools/validate.py response examples/valid/response_card.json --request examples/valid/request_roman_urdu_purchase.json
.venv/bin/python tests/test_spec.py
```

## License
- Specification text (`spec/`, and the prose in this README): [CC BY 4.0](LICENSE-SPEC).
- Schemas, tools, tests and demo code: [Apache License 2.0](LICENSE).

See [NOTICE](NOTICE).
