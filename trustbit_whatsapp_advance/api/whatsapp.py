import frappe
from trustbit_whatsapp_advance.utils.message_sender import send_whatsapp_message, send_template_message

@frappe.whitelist()
def send_message(recipient, message, reference_doctype=None, reference_name=None):
    """API to send a WhatsApp message"""
    return send_whatsapp_message(
        recipient=recipient,
        message=message,
        reference_doctype=reference_doctype,
        reference_name=reference_name
    )

@frappe.whitelist()
def send_from_template(template_name, doctype, docname):
    """API to send a message using a template"""
    doc = frappe.get_doc(doctype, docname)
    return send_template_message(template_name, doc)

@frappe.whitelist()
def get_templates(doctype=None):
    """Get available templates for a doctype"""
    filters = {"enabled": 1}
    if doctype:
        filters["reference_doctype"] = doctype
    
    return frappe.get_all("WhatsApp Template", filters=filters, fields=["name", "template_name", "reference_doctype"])
