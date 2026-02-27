import frappe
from frappe.model.document import Document


VALID_STATUSES = {"Pending", "Sent", "Delivered", "Read", "Failed", "Received"}


class WhatsAppMessageLog(Document):
    def before_insert(self):
        if not self.sent_at:
            self.sent_at = frappe.utils.now_datetime()

    def validate(self):
        if self.status and self.status not in VALID_STATUSES:
            frappe.throw(f"Invalid status: {self.status}")

    def update_status(self, status, message_id=None, error=None):
        """Update message status with validation."""
        if status not in VALID_STATUSES:
            return

        self.status = status
        if message_id:
            self.message_id = message_id
        if error:
            self.error_message = str(error)[:2000]

        if status == "Delivered":
            self.delivered_at = frappe.utils.now_datetime()
        elif status == "Read":
            self.read_at = frappe.utils.now_datetime()

        self.flags.ignore_permissions = True
        self.save()
