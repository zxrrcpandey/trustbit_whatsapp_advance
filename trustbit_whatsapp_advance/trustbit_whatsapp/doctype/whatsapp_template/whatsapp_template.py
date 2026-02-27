import frappe
from frappe.model.document import Document

class WhatsAppTemplate(Document):
    def validate(self):
        if not self.message_template and self.message_type == "Text":
            frappe.throw("Message Template is required for Text messages")
        
        if self.recipient_type == "Field" and not self.recipient_field:
            frappe.throw("Recipient Field is required when Recipient Type is Field")
    
    def get_message(self, doc):
        """Render the message template with document context"""
        from trustbit_whatsapp_advance.utils.template_renderer import render_template
        return render_template(self.message_template, doc)
