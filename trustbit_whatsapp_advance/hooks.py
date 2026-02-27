app_name = "trustbit_whatsapp_advance"
app_title = "Trustbit WhatsApp Advance"
app_publisher = "Trustbit"
app_description = "Advanced WhatsApp Integration for ERPNext with Two-Way Communication"
app_email = "info@trustbit.com"
app_license = "MIT"
app_version = "1.0.2"

# App JS (loaded on every desk page — provides the trustbit_whatsapp namespace)
app_include_js = "/assets/trustbit_whatsapp_advance/js/whatsapp.js"

# Required Apps
required_apps = ["frappe", "erpnext"]

# DocType JS Includes
doctype_js = {
    "Sales Order": "public/js/sales_order.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Quotation": "public/js/quotation.js",
    "Supplier Quotation": "public/js/supplier_quotation.js",
    "Material Request": "public/js/material_request.js",
    "Lead": "public/js/lead.js",
    "Project": "public/js/project.js",
    "Task": "public/js/task.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Purchase Receipt": "public/js/purchase_receipt.js"
}

# Document Events
doc_events = {
    "Sales Order": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Sales Invoice": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Purchase Order": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Purchase Invoice": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Quotation": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Supplier Quotation": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Material Request": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Lead": {
        "after_insert": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Project": {
        "after_insert": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Task": {
        "after_insert": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Delivery Note": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    },
    "Purchase Receipt": {
        "on_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event",
        "on_update_after_submit": "trustbit_whatsapp_advance.utils.notification_handler.handle_doc_event"
    }
}

# Scheduler Events
scheduler_events = {
    "cron": {
        "*/5 * * * *": [
            "trustbit_whatsapp_advance.utils.scheduler.process_pending_messages"
        ],
        "0 * * * *": [
            "trustbit_whatsapp_advance.utils.scheduler.update_message_status"
        ]
    },
    "daily": [
        "trustbit_whatsapp_advance.utils.scheduler.cleanup_old_logs"
    ]
}

# After Install
after_install = "trustbit_whatsapp_advance.setup.after_install"

# Fixtures
fixtures = []

# Jinja Environment
jenv = {
    "methods": [
        "trustbit_whatsapp_advance.utils.template_renderer.get_document_link"
    ]
}
