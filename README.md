# Trustbit WhatsApp Advance

Advanced WhatsApp Integration for ERPNext with Two-Way Communication

## Version
1.0.2

## Features
- Multi-provider support (360dialog, Gupshup, Twilio, Meta Direct)
- Send WhatsApp messages directly from Sales Order, Sales Invoice, Purchase Order, Purchase Invoice, Quotation, Supplier Quotation, Material Request, Delivery Note, Purchase Receipt, Lead, Project, and Task forms
- Template-based messaging with Jinja2 support
- Automatic notifications on document events (submit, update)
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
   - **API Key** — Your provider's App Secret (used for HMAC webhook verification)
   - **Access Token** — Permanent or temporary token for sending messages
   - **Phone Number ID** — Your WhatsApp Business phone number ID
   - **Business Account ID** — Your WhatsApp Business Account ID
   - **Webhook Verify Token** — A secret token you choose for webhook handshake verification
5. Save

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
