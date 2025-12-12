import frappe
import json

@frappe.whitelist(allow_guest=True)
def receive():
    """Webhook endpoint to receive WhatsApp messages and status updates"""
    try:
        # Handle GET request for webhook verification
        if frappe.request.method == "GET":
            return verify_webhook()
        
        # Handle POST request for incoming messages
        if frappe.request.method == "POST":
            return process_webhook()
    except Exception as e:
        frappe.log_error(f"Webhook error: {e}", "WhatsApp Webhook Error")
        return {"status": "error", "message": str(e)}

def verify_webhook():
    """Verify webhook for WhatsApp"""
    mode = frappe.request.args.get("hub.mode")
    token = frappe.request.args.get("hub.verify_token")
    challenge = frappe.request.args.get("hub.challenge")
    
    settings = frappe.get_single("WhatsApp Settings")
    
    if mode == "subscribe" and token == settings.webhook_verify_token:
        return challenge
    
    frappe.throw("Webhook verification failed", frappe.AuthenticationError)

def process_webhook():
    """Process incoming webhook data"""
    try:
        data = json.loads(frappe.request.data)
        
        # Update last webhook received
        settings = frappe.get_single("WhatsApp Settings")
        settings.db_set("last_webhook_received", frappe.utils.now_datetime())
        
        # Process the webhook data
        if "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    process_change(change)
        
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Webhook processing error: {e}", "WhatsApp Webhook Error")
        return {"status": "error", "message": str(e)}

def process_change(change):
    """Process a single change from webhook"""
    value = change.get("value", {})
    
    # Handle status updates
    statuses = value.get("statuses", [])
    for status in statuses:
        update_message_status(status)
    
    # Handle incoming messages
    messages = value.get("messages", [])
    for message in messages:
        process_incoming_message(message, value.get("contacts", []))

def update_message_status(status):
    """Update message log with delivery status"""
    message_id = status.get("id")
    new_status = status.get("status")
    
    status_map = {
        "sent": "Sent",
        "delivered": "Delivered",
        "read": "Read",
        "failed": "Failed"
    }
    
    mapped_status = status_map.get(new_status, new_status)
    
    # Find and update the message log
    logs = frappe.get_all("WhatsApp Message Log", filters={"message_id": message_id}, limit=1)
    if logs:
        log = frappe.get_doc("WhatsApp Message Log", logs[0].name)
        log.update_status(mapped_status)

def process_incoming_message(message, contacts):
    """Process an incoming message"""
    # Log incoming message
    frappe.log_error(f"Incoming WhatsApp message: {json.dumps(message)}", "WhatsApp Incoming")
