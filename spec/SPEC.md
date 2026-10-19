# MS Ads Sponsored Answer Spec v0.1 (draft)
Status: **DRAFT (v0.1.0-draft).** Extension to OpenRTB 2.6. Author: MS Ads Network. Date: 19 Oct 2026.
Schemas: `schema/sa-bid-request.schema.json`, `schema/sa-bid-response.schema.json`, `schema/sa-event.schema.json`. Validator: `validate.py`.
Overlap with AdCP Sponsored Intelligence and IAB Agentic Audiences: see `GAP_ANALYSIS.md`.

## 1. Purpose
Lets any chatbot, assistant or agent (the **host**) offer a labelled *sponsored answer* slot in a normal OpenRTB 2.6 auction, so existing DSPs can bid on a single conversational moment. The host never sends raw chat text or PII.

## 2. Where the objects live
| Object | Path | Required |
|---|---|---|
| Slot | `BidRequest.imp[].ext.sa` | yes |
| Agent and conversation | `BidRequest.ext.agent` | yes |
| Audience embeddings | `BidRequest.user.data[].segment[].ext.aa` (IAB Agentic Audiences; reused, not redefined) | optional |
| Sponsored answer | `BidResponse.seatbid[].bid[].ext.sa` | yes |
| Events | `POST /api/v1/agent-exchange/events` body (`sa-event`) | — |
Hosts use `app` (bundle = agent id) or `site` as usual. `source.schain` is required for resellers, as in OpenRTB.

## 3. `imp.ext.sa` (slot)
`ver` "0.1"; `formats` ⊂ {text, card, link}; `position` ∈ {after_answer, inline_suggestion, followup_chip}; `max_answers` 1–3; `max_text_chars` 40–600; `pricing` ⊂ {cpm, cpc, cpa}; `lite` (true = no image, or an image of 30 KB or less, for low bandwidth).
A sponsored answer is **never mixed into the organic answer text**; it is rendered as a separate block.

## 4. `ext.agent`
- `id`: registered agent id (never a secret key). `type` ∈ chatbot, assistant, voice_assistant, search_agent, task_agent, shopping_agent. `operator_domain`: must match the operator's `agent.json` / `app-ads.txt` entry.
- `conversation`:
  - `intent` ∈ informational, compare, decide, purchase, book, navigate, support, local_find. `decision_stage` ∈ explore, consider, decide, act (the "decision moment").
  - `summary` ≤ 200 characters, written by the agent, **no PII**.
  - `topic` {`cattax`, `cat`[], `keywords`[]}: use IAB Content Taxonomy (cattax 7 = CT 3.0). `0` = MS Ads internal, allowed only for transition.
  - `lang` {`code` ISO 639, `script` ISO 15924, `variant` standard/romanized/code_mixed, `mix`[], `reply_lang` BCP-47}. **Roman Urdu = `{"code":"ur","script":"Latn","variant":"romanized"}`**; Urdu-English mixed = `variant:"code_mixed", mix:["en"]`.
  - `turn` {`index`, `session_turns`, `prior_topics`[], `user_asked_for_options`, `modality`}: counts and categories only.
  - `sensitive`: true means the exchange **must not bid** (health, financial distress, politics, minors, crisis).
- `consent` {`ads` (required), `personalization`, `age_gate`, `gpp`, `gpp_sid`}. `ads=false` or `age_gate="minor"` means **no bid**.
- `disclosure` {`label_supported`: must be true, `label_lang`, `separate_ui`}.
- `ivt` (**filled by the exchange, never trusted from the host**): `checked` ⊂ D1–D6, `score` 0–100, `reasons` such as `D6.datacenter_ip`, `D5.token_invalid`, `D4.probation_cap`; `token` = D5 signed session token; `agent_verified`.
- `payout` {`statement_url`, `period`}: link to the operator's payout.json statement (Idea 3). Present only when the operator has one.

**Forbidden in an SA request** (rejected by the schema): `device.ip`, `device.ipv6`, `device.ifa`, `device.geo.lat/lon`, `user.id`, `user.buyeruid`. Country and connection type are allowed. The exchange keeps the IP *internally* for D1/D2/D6 and does not forward it.

## 5. Bid response `bid.ext.sa`
- `format`, `pricing`, and `offer_ref` (`axo_…`, the Agent Exchange reference).
- `disclosure` {`label` from an allowed list (Sponsored, Ad, Sponsored (ishtehar), اشتہار, Ishtehar, Sponsorlu, إعلان, विज्ञापन), `sponsor`, `placement` = `before_content`, `why_url`}.
- `answer` {`title`, `text` 10–600 characters, `lang`, `cta`, `url` https only, `image` (≤30 KB if `lite`), `price_claim` {amount, currency, valid_until}}.
- `events` {shown, clicked, accepted} URLs.
- `bid.price` is always the **CPM-equivalent** in `cur` (normal OpenRTB). The CPC or CPA price is settled through events. `adomain` is required.
- **Disclosure rules (checked by the validator):**
  - The label is shown before the content.
  - The sponsor name is visible.
  - The format and pricing are ones the slot allows.
  - The text length is within `max_text_chars`.
  - The answer language matches `reply_lang`.
  - There are no unverifiable superlatives ("world's #1", "first in the world", "guaranteed best").
  - There is no PII.
  - The price is at or above the floor.

## 6. Events
`shown` (sent after the block was on screen; `visible_ms` feeds D3 log-only viewability), `clicked`, and `accepted` (the user completed the action, i.e. a CPA task). Each event is idempotent through `idempotency_key`.
Mapping to the live Agent Exchange: shown→`impression`, clicked→`click` (or the `/ax/c/{ref}/{sig}` redirect), accepted→`task`.

## 7. Auction
v0.1 recommends `at=1` (first price): the winner pays its own bid. Since 19 Oct 2026 the MS Ads Agent Exchange also runs first price. `at=2` is still accepted, and the validator reports it as a note.

## 8. Compatibility with the live Agent Exchange (`msads-agent/0.1`)
- The change is purely additive. `msads_compat.py` adds `ext.agent` and `imp.ext.sa` to a live request and **keeps** `imp.native`, `imp.ext.msads_intent`, `msads_offer_request` and `ext.msads_agent`, so current DSPs are unaffected. It also strips any forbidden IDs.
- The test `LiveCompat` converts a real request shape from our load tests (`tests/fixture_live_msads_agent_0.1.json`) and validates it.
- Mapping: `msads_intent.task_type`→`intent`, `category`/`keywords`→`topic`, `language`→`lang.code`, `msads_offer_request.max_offers`/`pricing_models`→`imp.ext.sa`, `msads_agent.agent_id`/`agent_type`→`agent.id`/`type`.

## 9. Open items (v0.2)
- Map our internal categories to IAB Content Taxonomy 3.0.
- Map AdCP SI "sponsored response" products to this extension.
- Signed impression receipt (Idea 2) and payout.json schema (Idea 3).
- Voice rendering rules (spoken disclosure).
- An ARTF container for the language and IVT hooks.
