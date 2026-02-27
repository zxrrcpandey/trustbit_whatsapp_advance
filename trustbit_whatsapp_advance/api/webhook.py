import frappe
import json
import hashlib
import hmac

# Allowed status values from WhatsApp
VALID_STATUSES = {"sent", "delivered", "read", "failed"}
# Max webhook payload size (1 MB)
MAX_PAYLOAD_SIZE = 1_048_576


@frappe.whitelist(allow_guest=True)
def receive():
    """Webhook endpoint to receive WhatsApp messages and status updates.

    GET  — verification handshake (checks hub.verify_token)
    POST — incoming data (validates HMAC signature + verify token)
    """
    try:
        if frappe.request.method == "GET":
            return verify_webhook()

        if frappe.request.method == "POST":
            validate_webhook_signature()
            return process_webhook()

        frappe.throw("Method not allowed", frappe.AuthenticationError)
    except frappe.AuthenticationError:
        raise
    except Exception as e:
        frappe.log_error(f"Webhook error: {e}", "WhatsApp Webhook Error")
        return {"status": "error"}


def verify_webhook():
    """Verify webhook subscription (GET handshake from WhatsApp)."""
    mode = frappe.request.args.get("hub.mode")
    token = frappe.request.args.get("hub.verify_token")
    challenge = frappe.request.args.get("hub.challenge")

    if not mode or not token or not challenge:
        frappe.throw("Missing verification parameters", frappe.AuthenticationError)

    settings = frappe.get_single("WhatsApp Settings")

    if mode == "subscribe" and token == settings.get_password("webhook_verify_token"):
        return challenge

    frappe.throw("Webhook verification failed", frappe.AuthenticationError)


def validate_webhook_signature():
    """Validate the X-Hub-Signature-256 HMAC header on POST requests.

    Falls back to verify-token check if HMAC header is absent (some
    providers don't send it), but still requires the token to match.
    """
    settings = frappe.get_single("WhatsApp Settings")
    app_secret = settings.get_password("api_key") or ""
    raw_body = frappe.request.data or b""

    # Reject oversized payloads
    if len(raw_body) > MAX_PAYLOAD_SIZE:
        frappe.throw("Payload too large", frappe.AuthenticationError)

    # Check HMAC signature if header is present (Meta sends X-Hub-Signature-256)
    signature_header = frappe.request.headers.get("X-Hub-Signature-256", "")
    if signature_header:
        if not app_secret:
            frappe.log_error("HMAC header received but no API key configured", "WhatsApp Webhook Warning")
            frappe.throw("Webhook signature verification failed", frappe.AuthenticationError)

        expected_sig = "sha256=" + hmac.new(
            app_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature_header, expected_sig):
            frappe.throw("Invalid webhook signature", frappe.AuthenticationError)
        return  # HMAC valid — no further checks needed

    # Fallback: check verify token in query string or custom header
    token = (
        frappe.request.args.get("verify_token")
        or frappe.request.headers.get("X-Verify-Token", "")
    )
    stored_token = settings.get_password("webhook_verify_token")
    if stored_token and token and token == stored_token:
        return

    # If no HMAC and no token — log warning but allow (some providers send neither)
    frappe.log_error(
        "Webhook POST received without HMAC signature or verify token",
        "WhatsApp Webhook Warning"
    )


def process_webhook():
    """Process incoming webhook data after authentication."""
    try:
        raw = frappe.request.data
        if not raw:
            return {"status": "error", "message": "Empty payload"}

        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        frappe.log_error("Invalid JSON in webhook payload", "WhatsApp Webhook Error")
        return {"status": "error"}

    # Update last webhook received timestamp
    try:
        frappe.db.set_single_value(
            "WhatsApp Settings", "last_webhook_received", frappe.utils.now_datetime()
        )
    except Exception:
        pass  # Non-critical

    # Validate top-level structure
    if not isinstance(data, dict) or "entry" not in data:
        return {"status": "ok"}  # Nothing to process

    entries = data.get("entry")
    if not isinstance(entries, list):
        return {"status": "ok"}

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue
            try:
                process_change(change)
            except Exception as e:
                frappe.log_error(
                    f"Error processing webhook change: {e}", "WhatsApp Webhook Error"
                )

    frappe.db.commit()
    return {"status": "success"}


def process_change(change):
    """Process a single change from webhook."""
    value = change.get("value")
    if not isinstance(value, dict):
        return

    # Handle status updates
    for status in value.get("statuses", []):
        if isinstance(status, dict):
            update_message_status(status)

    # Handle incoming messages
    messages = value.get("messages", [])
    contacts = value.get("contacts", [])
    for message in messages:
        if isinstance(message, dict):
            process_incoming_message(message, contacts)


def update_message_status(status):
    """Update message log with delivery status."""
    message_id = status.get("id")
    new_status = status.get("status")

    if not message_id or not isinstance(message_id, str):
        return
    if new_status not in VALID_STATUSES:
        return

    status_map = {
        "sent": "Sent",
        "delivered": "Delivered",
        "read": "Read",
        "failed": "Failed",
    }
    mapped_status = status_map.get(new_status)
    if not mapped_status:
        return

    # Find and update the message log
    log_name = frappe.db.get_value(
        "WhatsApp Message Log", {"message_id": message_id}, "name"
    )
    if log_name:
        log = frappe.get_doc("WhatsApp Message Log", log_name)
        log.update_status(mapped_status)


def process_incoming_message(message, contacts):
    """Process an incoming WhatsApp message and store it."""
    message_id = message.get("id")
    sender = message.get("from")
    timestamp = message.get("timestamp")

    if not message_id or not sender:
        return

    # Validate sender is a plausible phone number (digits only, 7-15 chars)
    sender_clean = "".join(c for c in str(sender) if c.isdigit())
    if not (7 <= len(sender_clean) <= 15):
        return

    # Extract message text
    msg_type = message.get("type", "text")
    if msg_type == "text":
        body = (message.get("text") or {}).get("body", "")
    elif msg_type == "image":
        body = "[Image] " + (message.get("image") or {}).get("caption", "")
    elif msg_type == "document":
        body = "[Document] " + (message.get("document") or {}).get("filename", "")
    elif msg_type == "audio":
        body = "[Audio message]"
    elif msg_type == "video":
        body = "[Video] " + (message.get("video") or {}).get("caption", "")
    elif msg_type == "location":
        loc = message.get("location") or {}
        body = f"[Location] {loc.get('latitude', '')}, {loc.get('longitude', '')}"
    elif msg_type == "reaction":
        body = "[Reaction] " + (message.get("reaction") or {}).get("emoji", "")
    else:
        body = f"[{msg_type}]"

    # Truncate oversized messages
    if len(body) > 4096:
        body = body[:4093] + "..."

    # Get sender name from contacts array
    sender_name = ""
    if isinstance(contacts, list):
        for contact in contacts:
            if isinstance(contact, dict) and contact.get("wa_id") == sender:
                profile = contact.get("profile") or {}
                sender_name = profile.get("name", "")
                break

    # Check for duplicate (idempotent processing)
    if frappe.db.exists("WhatsApp Message Log", {"message_id": message_id}):
        return

    # Create incoming message log
    log = frappe.new_doc("WhatsApp Message Log")
    log.recipient = sender_clean
    log.recipient_name = sender_name[:140] if sender_name else ""
    log.message = body
    log.message_id = message_id
    log.status = "Received"
    log.sent_at = frappe.utils.now_datetime()
    log.flags.ignore_permissions = True
    log.insert()
