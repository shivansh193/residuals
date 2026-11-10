# Spikes

Verified before any UI is built. All PayPal calls hit the **sandbox** (`api-m.sandbox.paypal.com`).

| # | Spike | Status |
|---|-------|--------|
| 1 | Invoicing v2: create, send, pay, `INVOICING.INVOICE.PAID` webhook verifies | **Pass** (payment recorded via API, see note) |
| 2 | Payouts to a sandbox account: status + webhook | **Pass** |
| 3 | Speaker verification EER on 5 synthetic personas | **Pass**: utterance EER 0.0%, 1.5 s window EER 1.1% |
| 4 | Clone detector: designed voice vs zero-shot clone | **Partial**: wav2vec2 probe 89.8% (leave-one-persona-out); pretrained detector fails |

## 1 + 2: PayPal end to end (2026-11-10)

Hosted receiver: `https://residuals.onrender.com/webhooks/paypal` (Render). It's a dedicated sandbox webhook subscribed to `INVOICING.INVOICE.PAID` and the `PAYMENT.PAYOUTS*` events.

| Step | Result |
|------|--------|
| Create + send invoice (`POST /v2/invoicing/invoices`, `/send`) | `INV2-ZUEX-WQ8B-83WG-3C7B` sent to the sandbox buyer, with a payer-view link |
| Payment | Recorded with `POST /v2/invoicing/invoices/{id}/payments`, status `MARKED_AS_PAID` |
| Webhook `INVOICING.INVOICE.PAID` | Arrived on Render, `verify-webhook-signature` returned **SUCCESS** |
| Auto payout on PAID | Batch `VZ23939NA4FKG`, item `DHPKCJUTKTYJ4` **SUCCESS**, txn `21W108588R1973109`, $0.55 to the owner's sandbox account |
| Webhook `PAYMENT.PAYOUTS-ITEM.SUCCEEDED` | Arrived, verified |
| Retry behaviour | The first invoice's PAID event hit a server bug (500). PayPal retried on its own, and the retry verified and paid out (batch `C5CYSWUZBHA9N`) |
| Payout idempotency | Re-sending with the same `sender_batch_id` returns 400 `Batch with given sender_batch_id already exists`, with a link to the original batch. Using `roy-{invoice_id}` as the batch ID makes double payment impossible |

**Findings that change the design**

1. **Payout fees are per payout.** In sandbox, a $0.55 payout cost a $0.25 fee. Paying out per tiny use makes no sense, so royalties go to a ledger, and an owner payout is sent per paid invoice (one invoice can cover many segments). The fee is shown openly on the dashboard. A minimum-payout threshold or periodic batching is the production answer.
2. **Round each line to cents ourselves.** A fractional quantity (1.2333 min × $0.50) gave PayPal an item total of `0.617`, shown as `0.62`. Bill `quantity=1` with a pre-computed, cent-rounded amount and put the minutes in the description.
3. **Two event IDs per business event are possible** (original plus retry). Dedupe on the PayPal event ID, then on the invoice ID, before acting.
4. **Webhook resend** (`/webhooks-events/{id}/resend`) returned 404 for this app. We rely on PayPal's automatic retries plus a "reconcile" job that polls invoice status.

**Note on "pay as sandbox buyer".** Claude can't log in to PayPal with a password, so the invoice was marked paid through the API (`MARKED_AS_PAID`). That fires the same `INVOICING.INVOICE.PAID` event. For the video, a person should open the payer-view link and pay as the sandbox buyer to show the real checkout. The rest of the chain is identical.

## 3 + 4: voices (2026-11-11, Kaggle T4)

**Data.** There are 5 fictional personas. Each is a weighted blend of 2 Kokoro-82M voice packs, so no single real speaker. Each persona has:
- a 45 s enrolment passage;
- 40 sentences of "original" speech (Kokoro);
- the same 40 sentences as a zero-shot **F5-TTS** clone, made from a 6 s reference of that persona.

That's 400 test clips. Code: [kaggle/voice_spikes/kernel.py](../kaggle/voice_spikes/kernel.py) and [kaggle/pipeline/kernel.py](../kaggle/pipeline/kernel.py). Raw numbers: [fixtures/eval/spike_results.json](../fixtures/eval/spike_results.json).

### Spike 3: speaker verification (SpeechBrain ECAPA-TDNN)

| Trials (enrolment vs test clip) | EER | Threshold | Target mean / min | Non-target mean / max |
|---|---|---|---|---|
| Originals (200 target / 800 non-target) | 0.0% | 0.748 | 0.862 / 0.748 | 0.242 / 0.600 |
| **AI clones** (200 / 800) | **0.0%** | 0.684 | 0.821 / 0.684 | 0.221 / 0.554 |
| All (400 / 1600) | 0.0% | 0.684 | 0.841 / 0.684 | 0.231 / 0.600 |
| 1.5 s windows (what the pipeline uses) | 1.1% | 0.502 | | |

At the operating threshold, identification precision and recall are both 1.00 on whole clips. Two things stand out:
- **Clones still match their owner.** Clone scores average only 0.04 below originals. That is exactly what Residuals needs: an AI clone of Mara is still identified as Mara.
- **The set is easy.** Five synthetic voices are far apart. The closest pair is Mara and Ivy, at 0.58 enrolment similarity, because both blend female American Kokoro packs. Real voices, relatives and impersonators will be much closer. The 1.1% window EER is the more realistic figure.

### Spike 4: clone vs original

| Detector | Result |
|---|---|
| Pretrained `MelodyMachine/Deepfake-audio-detection-V2` (zero-shot) | Flagged **0%** of clones *and* 0% of the Kokoro originals as fake, so it's useless on this data. Both classes are modern TTS it never saw. |
| **wav2vec2-base features + logistic probe, leave-one-persona-out** | **89.8% accuracy**, 94.0% recall on clones, **14.5% false-positive rate** on originals. Per held-out persona: Theo 100%, Juno 100%, Silas 97.5%, Mara 85%, Ivy 66% |

**Decision.** The clone label is shown as a probability. It is never used to bill or block, because the owner's terms price use the same whether it's a clone or an original. It's evidence for the owner. A 14.5% false-positive rate is too high to accuse anyone. Important caveat: the "originals" here are themselves TTS, so this measures telling *Kokoro from F5-TTS*, not real voices from clones.

### End-to-end pipeline on 5 demo files (ground truth from the known composition)

VAD → 1.5 s/0.5 s ECAPA windows → enrolled-voice diarization → probe → Whisper → Gemini use type. Raw numbers: [fixtures/eval/pipeline_eval.json](../fixtures/eval/pipeline_eval.json).

| Metric | Result |
|---|---|
| Frame label accuracy in speech (which voice is speaking) | 87.6% mean (81.9% to 90.9%) |
| Minutes per (file, voice), 10 pairs | MAPE 10.8%; **always under-counts** (−12.9% overall), because window edges trim the start and end of each phrase |
| Segment clone label accuracy | 82.4% mean |
| Use type (Gemini) | 5/5 files; 40/40 labelled sentences |

**Decision.** Under-counting means under-billing, which is the safe direction for a royalty product. A later fix is to pad segments by half a window. Residuals never bills a match below the confidence threshold.
