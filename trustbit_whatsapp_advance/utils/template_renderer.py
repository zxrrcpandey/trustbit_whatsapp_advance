import frappe
from frappe.utils import fmt_money, getdate, get_datetime, format_date, format_datetime

def render_template(template, doc):
    """Render a Jinja template with document context"""
    if not template:
        return ""
    
    try:
        context = get_template_context(doc)
        return frappe.render_template(template, context)
    except Exception as e:
        frappe.log_error(f"Template rendering error: {e}", "WhatsApp Template Error")
        return template

def get_template_context(doc):
    """Get template context for rendering"""
    context = {
        "doc": doc,
        "frappe": frappe,
        "fmt_money": fmt_money,
        "getdate": getdate,
        "get_datetime": get_datetime,
        "format_date": format_date,
        "format_datetime": format_datetime,
        "nowdate": frappe.utils.nowdate,
        "now": frappe.utils.now,
        "get_url": frappe.utils.get_url
    }
    
    # Add company info
    if hasattr(doc, "company") and doc.company:
        context["company_doc"] = frappe.get_doc("Company", doc.company)
    
    return context

def get_document_link(doctype, name):
    """Get a link to view a document"""
    site_url = frappe.utils.get_url()
    return f"{site_url}/app/{frappe.scrub(doctype)}/{name}"
