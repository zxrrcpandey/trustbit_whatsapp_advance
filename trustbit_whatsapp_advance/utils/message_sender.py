import frappe
import json
from trustbit_whatsapp_advance.utils.whatsapp_api import get_api
from trustbit_whatsapp_advance.utils.template_renderer import render_template

def send_whatsapp_message(recipient, message, reference_doctype=None, reference_name=None, attach_file=None):
    """Send a WhatsApp message and log it"""
    
    # Create log entry
    log = frappe.new_doc("WhatsApp Message Log")
    log.recipient = recipient
    log.message = message
    log.reference_doctype = reference_doctype
    log.reference_name = reference_name
    log.status = "Pending"
    log.insert(ignore_permissions=True)
    frappe.db.commit()
    
    # Send message
    api = get_api()
    result = api.send_message(recipient, message, attach_file)
    
    # Update log
    if result.get("success"):
        log.status = "Sent"
        log.message_id = result.get("message_id")
    else:
        log.status = "Failed"
        log.error_message = result.get("error")
    
    log.provider_response = json.dumps(result.get("response", {}))
    log.save(ignore_permissions=True)
    frappe.db.commit()
    
    return result

def send_template_message(template_name, doc):
    """Send a message using a template"""
    template = frappe.get_doc("WhatsApp Template", template_name)
    
    if not template.enabled:
        return {"success": False, "error": "Template is disabled"}
    
    # Get recipient
    recipient = get_recipient(template, doc)
    if not recipient:
        return {"success": False, "error": "No recipient found"}
    
    # Render message
    message = render_template(template.message_template, doc)
    
    # Get attachment if needed
    attach_file = None
    if template.attach_pdf:
        attach_file = get_pdf_url(doc, template.pdf_print_format)
    
    # Send
    return send_whatsapp_message(
        recipient=recipient,
        message=message,
        reference_doctype=doc.doctype,
        reference_name=doc.name,
        attach_file=attach_file
    )

def get_recipient(template, doc):
    """Get recipient phone number based on template settings"""
    if template.recipient_type == "Field":
        return doc.get(template.recipient_field)
    elif template.recipient_type == "Owner":
        owner = frappe.get_doc("User", doc.owner)
        return owner.mobile_no
    elif template.recipient_type == "Assigned User":
        assignments = frappe.get_all("ToDo", filters={
            "reference_type": doc.doctype,
            "reference_name": doc.name,
            "status": "Open"
        }, fields=["allocated_to"])
        if assignments:
            user = frappe.get_doc("User", assignments[0].allocated_to)
            return user.mobile_no
    return None

def get_pdf_url(doc, print_format=None):
    """Generate PDF and return URL"""
    try:
        from frappe.utils.pdf import get_pdf
        from frappe.utils.file_manager import save_file
        
        html = frappe.get_print(doc.doctype, doc.name, print_format)
        pdf_content = get_pdf(html)
        
        file_name = f"{doc.doctype}-{doc.name}.pdf"
        file_doc = save_file(file_name, pdf_content, doc.doctype, doc.name, is_private=0)
        
        return frappe.utils.get_url() + file_doc.file_url
    except Exception as e:
        frappe.log_error(f"PDF generation error: {e}", "WhatsApp PDF Error")
        return None
