import frappe
from trustbit_whatsapp_advance.utils.message_sender import send_template_message
from trustbit_whatsapp_advance.utils.template_renderer import render_template

def handle_doc_event(doc, method):
    """Handle document events and trigger WhatsApp notifications"""
    
    # Check if WhatsApp is enabled
    try:
        settings = frappe.get_single("WhatsApp Settings")
        if not settings.enabled:
            return
    except Exception:
        return
    
    # Map method to event name
    event_map = {
        "after_insert": "after_insert",
        "on_update": "on_update",
        "on_submit": "on_submit",
        "on_cancel": "on_cancel",
        "on_update_after_submit": "on_update_after_submit"
    }
    
    event = event_map.get(method)
    if not event:
        return
    
    # Find matching notification rules
    rules = frappe.get_all("WhatsApp Notification Rule", filters={
        "enabled": 1,
        "reference_doctype": doc.doctype,
        "trigger_event": event
    }, fields=["name", "whatsapp_template", "condition"])
    
    for rule in rules:
        try:
            # Check condition
            if rule.condition:
                result = render_template(rule.condition, doc)
                if result.strip().lower() not in ["true", "1", "yes"]:
                    continue
            
            # Send message
            if settings.send_in_background:
                frappe.enqueue(
                    send_template_message,
                    template_name=rule.whatsapp_template,
                    doc=doc,
                    queue="short"
                )
            else:
                send_template_message(rule.whatsapp_template, doc)
        except Exception as e:
            frappe.log_error(f"WhatsApp notification error for {rule.name}: {e}", "WhatsApp Error")
