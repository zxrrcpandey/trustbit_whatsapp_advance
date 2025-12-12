import frappe
from frappe.utils import add_days, nowdate

def process_pending_messages():
    """Process pending messages in queue"""
    pass

def update_message_status():
    """Update status of sent messages"""
    pass

def cleanup_old_logs():
    """Clean up old message logs"""
    try:
        settings = frappe.get_single("WhatsApp Settings")
        retention_days = settings.message_log_retention_days or 90
        
        cutoff_date = add_days(nowdate(), -retention_days)
        
        frappe.db.sql("""
            DELETE FROM `tabWhatsApp Message Log`
            WHERE creation < %s
        """, (cutoff_date,))
        
        frappe.db.commit()
        
        settings.db_set("last_cleanup_date", nowdate())
    except Exception as e:
        frappe.log_error(f"WhatsApp log cleanup error: {e}", "WhatsApp Cleanup Error")
