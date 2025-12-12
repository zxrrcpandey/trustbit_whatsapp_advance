import frappe
from frappe.model.document import Document

class WhatsAppMessageLog(Document):
    def before_insert(self):
        if not self.sent_at:
            self.sent_at = frappe.utils.now_datetime()
    
    def update_status(self, status, message_id=None, error=None):
        """Update message status"""
        self.status = status
        if message_id:
            self.message_id = message_id
        if error:
            self.error_message = str(error)
        
        if status == "Delivered":
            self.delivered_at = frappe.utils.now_datetime()
        elif status == "Read":
            self.read_at = frappe.utils.now_datetime()
        
        self.save(ignore_permissions=True)
