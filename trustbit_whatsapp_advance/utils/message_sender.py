import frappe
import json
from trustbit_whatsapp_advance.utils.whatsapp_api import get_api
from trustbit_whatsapp_advance.utils.template_renderer import render_template

# Max PDF generation time (seconds)
PDF_TIMEOUT_SECONDS = 60


def send_whatsapp_message(recipient, message, reference_doctype=None, reference_name=None, attach_file=None):
    """Send a WhatsApp message and log it.

    Creates a WhatsApp Message Log entry, sends via the configured provider,
    and updates the log with the result.
    """
    user = frappe.session.user

    # Create log entry
    log = frappe.new_doc("WhatsApp Message Log")
    log.recipient = recipient
    log.message = message
    log.reference_doctype = reference_doctype
    log.reference_name = reference_name
    log.status = "Pending"
    log.insert()
    frappe.db.commit()

    # Audit log
    frappe.logger("whatsapp").info(
        f"WhatsApp send | user={user} | recipient={recipient} | "
        f"ref={reference_doctype}/{reference_name} | log={log.name}"
    )

    # Send message
    api = get_api()
    result = api.send_message(recipient, message, attach_file)

    # Update log
    if result.get("success"):
        log.status = "Sent"
        log.message_id = result.get("message_id")
    else:
        log.status = "Failed"
        log.error_message = str(result.get("error", "Unknown error"))[:2000]

    provider_response = result.get("response", {})
    try:
        log.provider_response = json.dumps(provider_response, default=str)[:10000]
    except (TypeError, ValueError):
        log.provider_response = "{}"

    log.save()
    frappe.db.commit()

    return result


def send_template_message(template_name, doc):
    """Send a message using a WhatsApp Template.

    Renders the template with document context, resolves recipient,
    optionally attaches a PDF, and sends.
    """
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
        attach_file=attach_file,
    )


def get_recipient(template, doc):
    """Get recipient phone number based on template settings."""
    if template.recipient_type == "Field":
        value = doc.get(template.recipient_field)
        return str(value).strip() if value else None

    elif template.recipient_type == "Owner":
        mobile = frappe.db.get_value("User", doc.owner, "mobile_no")
        return mobile

    elif template.recipient_type == "Assigned User":
        assigned = frappe.db.get_value(
            "ToDo",
            {"reference_type": doc.doctype, "reference_name": doc.name, "status": "Open"},
            "allocated_to",
        )
        if assigned:
            return frappe.db.get_value("User", assigned, "mobile_no")

    return None


def get_pdf_url(doc, print_format=None):
    """Generate a PDF for the document and return its URL.

    Applies a size limit and timeout to prevent resource exhaustion.
    """
    try:
        from frappe.utils.pdf import get_pdf
        from frappe.utils.file_manager import save_file
        import signal

        html = frappe.get_print(doc.doctype, doc.name, print_format)

        # Truncate extremely large HTML before PDF conversion
        if len(html) > 500_000:
            frappe.log_error(
                f"HTML too large for PDF: {doc.doctype}/{doc.name} ({len(html)} chars)",
                "WhatsApp PDF Warning",
            )
            return None

        pdf_content = get_pdf(html)

        # Limit PDF size to 16 MB (WhatsApp limit)
        if len(pdf_content) > 16 * 1024 * 1024:
            frappe.log_error(
                f"PDF too large: {doc.doctype}/{doc.name} ({len(pdf_content)} bytes)",
                "WhatsApp PDF Warning",
            )
            return None

        file_name = f"{doc.doctype}-{doc.name}.pdf"
        file_doc = save_file(file_name, pdf_content, doc.doctype, doc.name, is_private=0)

        return frappe.utils.get_url() + file_doc.file_url
    except Exception as e:
        frappe.log_error(f"PDF generation error: {e}", "WhatsApp PDF Error")
        return None
