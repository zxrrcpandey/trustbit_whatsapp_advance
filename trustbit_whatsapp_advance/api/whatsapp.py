import frappe
from frappe import _
import re
from trustbit_whatsapp_advance.utils.message_sender import send_whatsapp_message, send_template_message

# Phone number regex: 7-15 digits, optionally with leading +
PHONE_REGEX = re.compile(r"^\+?\d{7,15}$")

# Max message length (WhatsApp limit)
MAX_MESSAGE_LENGTH = 4096

# Allowed doctypes for template-based sending
ALLOWED_DOCTYPES = {
    "Sales Order", "Sales Invoice", "Purchase Order", "Purchase Invoice",
    "Quotation", "Supplier Quotation", "Material Request", "Lead",
    "Project", "Task", "Delivery Note", "Purchase Receipt",
}

# Rate limit: max messages per user per minute
RATE_LIMIT_PER_MINUTE = 30


def _check_rate_limit():
    """Check if the current user has exceeded the message rate limit."""
    user = frappe.session.user
    cache_key = f"whatsapp_rate:{user}"
    count = frappe.cache.get_value(cache_key) or 0

    if count >= RATE_LIMIT_PER_MINUTE:
        frappe.throw(
            _("Rate limit exceeded. Please wait before sending more messages."),
            frappe.RateLimitExceededError if hasattr(frappe, "RateLimitExceededError") else frappe.ValidationError,
        )

    frappe.cache.set_value(cache_key, count + 1, expires_in_sec=60)


def _validate_phone(phone):
    """Validate phone number format."""
    if not phone or not isinstance(phone, str):
        frappe.throw(_("Recipient phone number is required"))

    cleaned = phone.strip()
    if not PHONE_REGEX.match(cleaned):
        frappe.throw(_("Invalid phone number format. Use 7-15 digits, optionally prefixed with +"))

    return cleaned


def _validate_message(message):
    """Validate message content."""
    if not message or not isinstance(message, str):
        frappe.throw(_("Message is required"))

    message = message.strip()
    if not message:
        frappe.throw(_("Message cannot be empty"))

    if len(message) > MAX_MESSAGE_LENGTH:
        frappe.throw(_("Message exceeds maximum length of {0} characters").format(MAX_MESSAGE_LENGTH))

    return message


@frappe.whitelist()
def send_message(recipient, message, reference_doctype=None, reference_name=None):
    """API to send a WhatsApp message.

    Args:
        recipient: Phone number (7-15 digits)
        message: Message text (max 4096 chars)
        reference_doctype: Optional linked DocType
        reference_name: Optional linked document name
    """
    _check_rate_limit()
    recipient = _validate_phone(recipient)
    message = _validate_message(message)

    # Validate reference document if provided
    if reference_doctype and reference_name:
        if reference_doctype not in ALLOWED_DOCTYPES:
            frappe.throw(_("DocType '{0}' is not allowed for WhatsApp messages").format(reference_doctype))

        if not frappe.db.exists(reference_doctype, reference_name):
            frappe.throw(_("Document {0} {1} not found").format(reference_doctype, reference_name))

        # Check user has read permission on the document
        if not frappe.has_permission(reference_doctype, "read", reference_name):
            frappe.throw(_("You do not have permission to access this document"), frappe.PermissionError)

    return send_whatsapp_message(
        recipient=recipient,
        message=message,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
    )


@frappe.whitelist()
def send_from_template(template_name, doctype, docname):
    """API to send a message using a template.

    Args:
        template_name: Name of WhatsApp Template
        doctype: DocType of the source document
        docname: Name of the source document
    """
    _check_rate_limit()

    # Validate doctype
    if not doctype or doctype not in ALLOWED_DOCTYPES:
        frappe.throw(_("DocType '{0}' is not allowed for WhatsApp messages").format(doctype))

    # Validate document exists
    if not docname or not frappe.db.exists(doctype, docname):
        frappe.throw(_("Document {0} {1} not found").format(doctype, docname))

    # Check user has read permission on the document
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("You do not have permission to access this document"), frappe.PermissionError)

    # Validate template exists and is enabled
    if not frappe.db.exists("WhatsApp Template", template_name):
        frappe.throw(_("Template '{0}' not found").format(template_name))

    doc = frappe.get_doc(doctype, docname)
    return send_template_message(template_name, doc)


@frappe.whitelist()
def get_templates(doctype=None):
    """Get available WhatsApp templates, optionally filtered by doctype."""
    filters = {"enabled": 1}
    if doctype:
        if doctype not in ALLOWED_DOCTYPES:
            frappe.throw(_("Invalid doctype"))
        filters["reference_doctype"] = doctype

    return frappe.get_all(
        "WhatsApp Template",
        filters=filters,
        fields=["name", "template_name", "reference_doctype"],
    )
