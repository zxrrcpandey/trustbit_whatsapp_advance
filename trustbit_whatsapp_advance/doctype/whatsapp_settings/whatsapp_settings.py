import frappe
from frappe.model.document import Document

class WhatsAppSettings(Document):
    def validate(self):
        if self.enabled:
            if not self.api_key:
                frappe.throw("API Key is required when WhatsApp is enabled")
            if not self.phone_number_id:
                frappe.throw("Phone Number ID is required when WhatsApp is enabled")
    
    def on_update(self):
        # Generate webhook URL
        site_url = frappe.utils.get_url()
        self.db_set("webhook_url", f"{site_url}/api/method/trustbit_whatsapp_advance.api.webhook.receive")
