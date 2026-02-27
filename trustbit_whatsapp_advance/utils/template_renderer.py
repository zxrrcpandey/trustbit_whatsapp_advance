import frappe
from frappe.utils import fmt_money, getdate, get_datetime, format_date, format_datetime


def render_template(template, doc):
    """Render a Jinja template with a restricted document context.

    The context deliberately excludes the ``frappe`` module and other
    dangerous objects to prevent template-injection attacks.  Only safe
    formatting helpers and the document itself are exposed.
    """
    if not template:
        return ""

    if not isinstance(template, str):
        return ""

    # Quick sanity check: reject obviously malicious patterns
    dangerous_patterns = [
        "__import__", "__builtins__", "__class__", "__subclasses__",
        "os.system", "subprocess", "eval(", "exec(",
        "frappe.db", "frappe.client", "frappe.utils.safe_exec",
    ]
    template_lower = template.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in template_lower:
            frappe.log_error(
                f"Blocked dangerous template pattern: {pattern}",
                "WhatsApp Template Security",
            )
            return "[Template blocked for security reasons]"

    try:
        context = get_template_context(doc)
        return frappe.render_template(template, context)
    except Exception as e:
        frappe.log_error(f"Template rendering error: {e}", "WhatsApp Template Error")
        return "[Template rendering failed]"


def get_template_context(doc):
    """Build a safe template context — no frappe module exposed."""
    context = {
        "doc": doc,
        "fmt_money": fmt_money,
        "getdate": getdate,
        "get_datetime": get_datetime,
        "format_date": format_date,
        "format_datetime": format_datetime,
        "nowdate": frappe.utils.nowdate,
        "now": frappe.utils.now,
        "get_url": frappe.utils.get_url,
    }

    # Add company info (read-only dict, not the full Doc object)
    if hasattr(doc, "company") and doc.company:
        try:
            company = frappe.get_doc("Company", doc.company)
            context["company_doc"] = {
                "name": company.name,
                "company_name": company.company_name,
                "phone_no": company.phone_no,
                "email": company.email,
                "website": company.website,
                "tax_id": company.tax_id,
                "domain": company.domain,
                "default_currency": company.default_currency,
            }
        except Exception:
            pass

    return context


def get_document_link(doctype, name):
    """Get a URL link to view a document."""
    if not doctype or not name:
        return ""
    site_url = frappe.utils.get_url()
    return f"{site_url}/app/{frappe.scrub(doctype)}/{name}"
