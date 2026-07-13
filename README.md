# Trustbit WhatsApp Advance

Advanced WhatsApp Integration for ERPNext with Two-Way Communication

## Version
1.0.1

> **Note:** `hooks.py` declares `app_version = "1.0.2"`, but the package version in `setup.py`, `pyproject.toml`, and `__init__.py` is still 1.0.1 — this is what `bench version` reports. The effective installed version is **1.0.1** until the packaging files are bumped.

## Features
- Multi-provider support (360dialog, Gupshup, Twilio, Meta Direct)
- Send WhatsApp messages directly from Sales Order, Sales Invoice, Purchase Order, Purchase Invoice, Quotation, Supplier Quotation, Material Request, Delivery Note, Purchase Receipt, Lead, Project, and Task forms
- Template-based messaging with Jinja2 support
- Automatic notifications on document events (submit and post-submit update for transaction documents; creation and update for Lead, Project, and Task)
- Two-way communication with incoming message processing via webhook
- HMAC signature verification for webhook security
- Message logging with delivery status tracking (Pending, Sent, Delivered, Read, Failed, Received)
- PDF attachment support
- Retry logic for failed/pending messages (up to 3 retries)
- Automatic cleanup of old message logs (configurable retention period)

## Installation

```bash
bench get-app https://github.com/zxrrcpandey/trustbit_whatsapp_advance.git
bench --site your-site install-app trustbit_whatsapp_advance
bench --site your-site migrate
bench build
sudo supervisorctl restart all
```

## Configuration

### Basic Setup
1. Search **"WhatsApp Settings"** in the awesomebar
2. Check **Enabled**
3. Select your **Provider** (e.g., Meta Direct)
4. Enter your **API credentials**:
   - **API Key** — a single field that plays two roles:
     - *Sending credential* (what to enter depends on the provider):
       - **Meta Direct** — your permanent or temporary Access Token (sent as `Authorization: Bearer`)
       - **360dialog** — your `D360-API-KEY`
       - **Gupshup** — your `apikey`
       - **Twilio** — your Auth Token (used for basic auth together with the Account SID, see Business Account ID below)
     - *Webhook HMAC secret* — the same value is used as the app secret to verify the `X-Hub-Signature-256` header on incoming webhook POSTs
   - **Phone Number ID** — Your WhatsApp Business phone number ID
   - **Business Account ID** — Your WhatsApp Business Account ID (for Twilio, enter the Account SID here)
   - **Webhook Verify Token** — A secret token you choose for webhook handshake verification
5. Save

> **Meta Direct limitation:** Meta uses two *different* credentials — the Access Token (for sending) and the App Secret (for webhook signatures). Since there is only one API Key field, you cannot configure both correctly at once: with the Access Token stored (required for sending), Meta's signed webhook POSTs will fail HMAC verification, because the signature is computed with the App Secret. Only webhook requests without a signature header fall back to the verify-token check. For the other providers the sending credential and HMAC secret are the same value, so there is no conflict.

### Meta Direct Webhook Setup
1. Go to [Meta Developer Console](https://developers.facebook.com/) > Your App > WhatsApp > Configuration
2. Set **Callback URL** to:
   ```
   https://your-site.com/api/method/trustbit_whatsapp_advance.api.webhook.verify
   ```
3. Set **Verify Token** to the same value you entered in WhatsApp Settings
4. Click **Verify and Save**
5. Subscribe to the **messages** webhook field

## Supported DocTypes
The WhatsApp "Send" button appears on the following forms:
- Sales Order
- Sales Invoice
- Purchase Order
- Purchase Invoice
- Quotation
- Supplier Quotation
- Material Request
- Delivery Note
- Purchase Receipt
- Lead
- Project
- Task

## Scheduler Jobs
| Schedule | Task | Description |
|----------|------|-------------|
| Every 5 minutes | `process_pending_messages` | Retries messages stuck in Pending status (max 3 retries) |
| Hourly | `update_message_status` | Flags messages sent over 24 hours ago with no delivery confirmation |
| Daily | `cleanup_old_logs` | Removes message logs older than the configured retention period |

## Webhook Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `.api.webhook.verify` | GET | Meta webhook verification handshake (returns raw challenge) |
| `.api.webhook.receive` | GET/POST | Incoming messages and status updates processing |

## Security
- HMAC-SHA256 signature verification on incoming webhooks
- Webhook verify token stored as Password field (encrypted)
- Rate limiting on outbound message API (30 messages/user/minute)
- Input validation on phone numbers and message content
- Permission checks on document access before sending

## License
MIT
