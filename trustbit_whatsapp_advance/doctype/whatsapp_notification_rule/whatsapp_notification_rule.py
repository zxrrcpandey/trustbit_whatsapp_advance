import frappe
from frappe.model.document import Document

class WhatsAppNotificationRule(Document):
    def validate(self):
        if not self.whatsapp_template:
            frappe.throw("WhatsApp Template is required")
    
    def check_condition(self, doc):
        """Check if the condition is met for the document"""
        if not self.condition:
            return True
        
        try:
            from trustbit_whatsapp_advance.utils.template_renderer import render_template
            result = render_template(self.condition, doc)
            return result.strip().lower() in ["true", "1", "yes"]
        except Exception:
            return False
