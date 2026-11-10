# Residuals

**Royalties for licensed AI voice clones, paid through PayPal.**

Live demo: **https://residuals.onrender.com** (PayPal **sandbox**; no real money moves) · API docs: [/docs](https://residuals.onrender.com/docs) · Licence: MIT

A voice owner enrols their own voice and sets terms in plain English: *"$30 a minute for ads, free for non-profits, never for politics."* Residuals finds that voice in submitted audio, even when it's an AI clone, and measures the minutes. It bills the user with a **PayPal invoice**. When the invoice is paid, PayPal's signed webhook triggers a **PayPal Payout** of the royalty to the owner. Unlicensed use gets a one-click retroactive licence offer instead of a lawsuit. Blocked uses, such as political ads, get no offer: the owner is alerted with the evidence.

> **The one rule: consent first.** Only voices whose owners enrolled themselves, with a consent recording and a live liveness phrase, can be registered. Every voice in this demo is a fictional, **fully synthetic** persona. No real person's voice was recorded or cloned ([ASSETS.md](ASSETS.md)).

## The problem

AI voice clones are cheap and everywhere, but the people they belong to rarely know where they're used, and rarely get paid. Sources are in [docs/RESEARCH.md](docs/RESEARCH.md):

- Voice actors Paul Lehrman and Linnea Sage say they discovered AI clones of their voices being sold by Lovo. Lehrman heard his own voice in a YouTube video and a podcast he never recorded ([CBS News](https://www.cbsnews.com/news/two-voice-actors-sue-ai-company-lovo)).
- The law is moving toward consent and compensation:
  - Tennessee's **ELVIS Act** (in force since July 2024) protects voice, real or simulated.
  - The federal **NO FAKES Act of 2026** cleared Senate Judiciary in June 2026 but is not law yet.
  - The **SAG-AFTRA 2025 video-game agreement** requires consent, plus usage reports that show how digital-replica pay was calculated.
  - The **EU AI Act Art. 50** requires synthetic audio to be marked from 2 August 2026.
- Existing tools each cover one piece:
  - ElevenLabs has paid voice creators over $22M, but only for use inside ElevenLabs.
  - YouTube's likeness detection and tools like Pex detect voices but don't pay anyone.
  - Nothing combines **cross-platform use metering + owner-set licence terms + automatic per-use payment**. Residuals is that missing layer.

## Try it (no setup)

1. **Pre-clear audio** → pick *Brightline Appliances* and the *spring campaign* ad → **Scan**. The Bryntum timeline shows Mara Vell's voice as an **AI clone**, and the pre-clearance prices each voice under its owner's terms.
2. In the PayPal panel, either:
   - **Pay with PayPal** as the sandbox buyer (see *Sandbox accounts* below), or
   - **Mark paid (sandbox)**, which records the payment through the PayPal API.

   Either way, PayPal sends `INVOICING.INVOICE.PAID`, we verify the signature, and a **Payout** goes to the owner. The panel shows each PayPal ID as it happens.
3. Scan the *QuickClips* video as *QuickClips Media*: no licences, so you get a **retroactive licence offer**. Scan the *Measure 12* spot: **blocked**, with no offer and an alert to the owner.
4. **Voice owner** → the owner's AG Grid ledger, royalties paid, alerts, and a hash-chain integrity check.
5. **Enrol a voice** → record a consent statement and a random liveness phrase; Gemini verifies them. Then type terms in plain English and Gemini turns them into a policy.

## Architecture

```
Browser (React + Vite)
  ├─ Pre-clear portal ── Bryntum Scheduler timeline + wavesurfer waveform
  ├─ Owner dashboard ─── AG Grid ledger
  └─ Enrolment ───────── MediaRecorder → /api/enrol (Gemini consent + liveness check)
        │
FastAPI on Render (server/)
  ├─ policy.py    Gemini: plain-English terms → structured policy (owner confirms)
  ├─ billing.py   pure decision + pricing logic (unit-tested)
  ├─ service.py   scan → ledger (SHA-256 hash chain) → PayPal invoice; PAID → Payouts
  ├─ paypal.py    OAuth, Invoicing v2, Payouts, webhook signature verification
  └─ /webhooks/paypal   INVOICING.INVOICE.PAID, PAYMENT.PAYOUTS-ITEM.*
        │
Kaggle GPU (kaggle/)  — heavy models, results cached into fixtures/
  voice_spikes/  synthetic personas (Kokoro voice blends) + zero-shot clones (F5-TTS)
  pipeline/      VAD → ECAPA enrolled-voice diarization → clone detector → Whisper ASR → eval
```

The speech models need a GPU, so the five demo files are analysed in advance on Kaggle ([kaggle/pipeline/kernel.py](kaggle/pipeline/kernel.py)), and the results are stored in `fixtures/analysis/`. Everything after detection runs live on Render: policy lookup, decisions, PayPal invoicing, webhooks, payouts and the ledger.

## PayPal APIs used (sandbox)

| API | Where | What for |
|-----|-------|----------|
| OAuth2 client credentials | `server/paypal.py` | access tokens (cached) |
| **Invoicing v2** `POST /v2/invoicing/invoices`, `/send` | `service.create_invoice` | one invoice per scan; one line per voice, cent-rounded; `PayPal-Request-Id = inv-{scan}` for idempotency |
| Invoicing v2 `POST /invoices/{id}/payments` | `service.sandbox_mark_paid` | sandbox shortcut for judges without a buyer login |
| **Webhooks** `INVOICING.INVOICE.PAID`, `PAYMENT.PAYOUTS-ITEM.SUCCEEDED/FAILED/UNCLAIMED` | `app.paypal_webhook` | every event verified with `POST /v1/notifications/verify-webhook-signature`; deduped by event ID |
| **Payouts** `POST /v1/payments/payouts` | `service.on_invoice_paid` | royalty to each owner; `sender_batch_id = roy-{invoice}-{voice}`, so a retry can never pay twice |

The platform fee (10%) is shown on every ledger row, and so is PayPal's payout fee when the payout webhook reports it. Spike results, including the decisions they forced, are in [docs/SPIKES.md](docs/SPIKES.md).

## AI components

| Step | Model | Runs on |
|------|-------|---------|
| Voice activity detection | Silero VAD | Kaggle GPU |
| Speaker embeddings + enrolled-voice diarization | SpeechBrain ECAPA-TDNN (`spkrec-ecapa-voxceleb`), 1.5 s windows, calibrated threshold | Kaggle GPU |
| Clone vs original | wav2vec2-base features + logistic probe, evaluated leave-one-persona-out; a pretrained deepfake detector as a baseline | Kaggle GPU |
| Transcription | Whisper small | Kaggle GPU |
| Use-type classification | Gemini, structured output | live (cached for demo files) |
| Terms → policy | Gemini, structured output, owner confirms | live |
| Consent + liveness check | Gemini audio understanding + string match against a random, single-use phrase | live |

## Evaluation

Small and synthetic, and honest about it: 5 fictional personas, 400 test clips (200 Kokoro "originals", 200 F5-TTS zero-shot clones), and 5 demo files with ground truth built from their known composition. Full write-up: [docs/SPIKES.md](docs/SPIKES.md). Raw numbers: [fixtures/eval/](fixtures/eval).

| What | Result |
|---|---|
| **Speaker match** (ECAPA), whole clips | EER **0.0%** for originals and for AI clones; precision **1.00** / recall **1.00** at the operating threshold |
| Speaker match, 1.5 s windows (as the pipeline uses) | EER **1.1%** |
| Clones still match their owner | clone scores average 0.82 vs 0.86 for originals; the highest impostor score is 0.60 |
| **Clone detection**, wav2vec2 probe, leave-one-persona-out | **89.8%** accuracy, **14.5%** false positives on originals (Ivy is the weakest persona, at 66%) |
| Clone detection, pretrained deepfake model (zero-shot) | flagged 0% of anything as fake, so it fails on modern TTS |
| **Minutes** per voice per file (10 pairs) | MAPE **10.8%**; always under-counts (−12.9% overall), which is the safe direction for billing |
| Who-is-speaking, frame accuracy | 87.6% |
| **Use type** (Gemini) | 5/5 demo files, 40/40 labelled sentences (clear-cut sentences, so an easy set) |
| **Billing** | 12 tests: decisions, cent rounding, the fee never takes the owner's rounding cent, retry-safe payouts (no double pay), hash-chain tamper detection |
| PayPal sandbox, end to end | invoice → signed `INVOICING.INVOICE.PAID` → Payout `SUCCESS` → signed `PAYMENT.PAYOUTS-ITEM.SUCCEEDED`; PayPal's own retry was handled correctly |

What these numbers don't show: real human voices, noisy or compressed audio, music beds, deliberate evasion, or voices that sound alike. See *Limitations*.

## Consent and privacy

- Consent first: self-enrolment only, with a consent statement and a random single-use liveness phrase. The phrase is matched in code, not only by the LLM.
- Detections below the confidence threshold are **never billed automatically**. They go to the owner as "needs review".
- Demo voices are fictional personas, blended from Kokoro-82M voice packs and cloned only from themselves.
- No audio leaves the owner's enrolment except to Gemini for the consent check. Secrets live in environment variables, and a secret scan runs before every push.

## Limitations (honest)

- **Small, synthetic eval set.** There are 5 synthetic personas. The "originals" are themselves TTS (Kokoro) and the "clones" are F5-TTS zero-shot copies, so clone detection here means telling two synthesis systems apart, not real recordings from fakes. A real deployment needs real enrolled speakers and an ASVspoof-style eval.
- **Adversarial evasion.** Pitch or formant shifting, heavy effects, music beds, or a different clone model could lower match scores. This is the main reason below-threshold matches go to the owner rather than being billed.
- **Similar voices.** Relatives, and the kind of voice blending used to make these personas, produce similar embeddings. Look at the enrolment similarity matrix in `fixtures/eval/spike_results.json`.
- **Live scanning of new uploads** needs the GPU worker. The hosted demo scans pre-analysed demo files, and new enrolments stay `pending_voiceprint` until the worker runs.
- **Ephemeral storage.** The hosted demo uses SQLite on Render's free tier, so the ledger resets when the service redeploys.
- One sandbox receiver account stands in for all five persona owners.

## Run it yourself

```bash
cp .env.example .env    # PayPal sandbox app, webhook id, Gemini key
pip install -r requirements.txt
uvicorn server.app:app --reload
cd web && npm install && npm run dev    # Bryntum trial: set BRYNTUM_NPM_TOKEN (see web/.npmrc)
python -m pytest tests
```

Kaggle: [`kaggle/voice_spikes`](kaggle/voice_spikes/kernel.py) builds the personas and clones, and [`kaggle/pipeline`](kaggle/pipeline/kernel.py) runs detection and evaluation. `python scripts/ingest_pipeline.py <kernel output>` writes the results to `fixtures/`.

SDKs for platforms, generated with **APIMatic** from the OpenAPI spec: [`sdk/python`](sdk/python), [`sdk/typescript`](sdk/typescript).

### Sandbox accounts for judges

SANDBOX_PLACEHOLDER

## Built with

PayPal (Invoicing v2, Payouts, Webhooks) · Gemini · SpeechBrain ECAPA-TDNN · Silero VAD · Whisper · wav2vec2 · Kokoro-82M · F5-TTS · AG Grid · Bryntum Scheduler · Render · APIMatic · FastAPI · React · Kaggle

MIT licence. Bryntum is used under its trial licence (watermarked).
