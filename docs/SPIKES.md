# Spikes

Verified before any UI is built. All PayPal calls hit the **sandbox** (`api-m.sandbox.paypal.com`).

| # | Spike | Status |
|---|-------|--------|
| 1 | Invoicing v2: create, send, pay, `INVOICING.INVOICE.PAID` webhook verifies | **Pass** (payment recorded via API, see note) |
| 2 | Payouts to a sandbox account: status + webhook | **Pass** |
| 3 | Speaker verification EER on synthetic personas | Running on Kaggle (queued for GPU) |
| 4 | Clone detector: designed voice vs zero-shot clone | Running on Kaggle (queued for GPU) |

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
