// WhatsApp Integration for ERPNext
frappe.provide("trustbit_whatsapp");

trustbit_whatsapp.send_message = function(frm) {
    // Get recipient from document (may be empty)
    let recipient_field = get_recipient_field(frm.doctype);
    let recipient = frm.doc[recipient_field] || "";

    // Show dialog (always opens, even without a number)
    let d = new frappe.ui.Dialog({
        title: __("Send WhatsApp Message"),
        fields: [
            {
                fieldname: "recipients",
                fieldtype: "Small Text",
                label: __("Recipient(s)"),
                default: recipient,
                reqd: 1,
                description: __("Enter one or more phone numbers, separated by comma or new line")
            },
            {
                fieldname: "template",
                fieldtype: "Link",
                label: __("Template"),
                options: "WhatsApp Template",
                get_query: function() {
                    return {
                        filters: {
                            reference_doctype: frm.doctype,
                            enabled: 1
                        }
                    };
                }
            },
            {
                fieldname: "message",
                fieldtype: "Text",
                label: __("Message"),
                reqd: 1
            }
        ],
        primary_action_label: __("Send"),
        primary_action: function(values) {
            // Parse multiple numbers (comma or newline separated)
            let numbers = values.recipients
                .split(/[,\n]+/)
                .map(function(n) { return n.trim(); })
                .filter(function(n) { return n.length > 0; });

            if (numbers.length === 0) {
                frappe.msgprint(__("Please enter at least one phone number"));
                return;
            }

            d.disable_primary_action();
            let sent = 0;
            let failed = 0;
            let total = numbers.length;

            function send_next(index) {
                if (index >= total) {
                    d.enable_primary_action();
                    if (failed === 0) {
                        frappe.msgprint(__("Message sent successfully to {0} recipient(s)!", [sent]));
                    } else {
                        frappe.msgprint(__("Sent to {0}, failed for {1} recipient(s)", [sent, failed]));
                    }
                    d.hide();
                    return;
                }

                frappe.call({
                    method: "trustbit_whatsapp_advance.api.whatsapp.send_message",
                    args: {
                        recipient: numbers[index],
                        message: values.message,
                        reference_doctype: frm.doctype,
                        reference_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            sent++;
                        } else {
                            failed++;
                        }
                        send_next(index + 1);
                    },
                    error: function() {
                        failed++;
                        send_next(index + 1);
                    }
                });
            }

            send_next(0);
        }
    });

    // Load template message if selected
    d.fields_dict.template.$input.on("change", function() {
        let template = d.get_value("template");
        if (template) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "WhatsApp Template",
                    name: template
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.call({
                            method: "frappe.utils.jinja.render_template",
                            args: {
                                template: r.message.message_template,
                                context: {doc: frm.doc}
                            },
                            callback: function(r2) {
                                if (r2.message) {
                                    d.set_value("message", r2.message);
                                }
                            }
                        });
                    }
                }
            });
        }
    });

    d.show();
};

function get_recipient_field(doctype) {
    const field_map = {
        "Sales Order": "contact_mobile",
        "Sales Invoice": "contact_mobile",
        "Purchase Order": "contact_mobile",
        "Purchase Invoice": "contact_mobile",
        "Quotation": "contact_mobile",
        "Supplier Quotation": "contact_mobile",
        "Material Request": "contact_mobile",
        "Delivery Note": "contact_mobile",
        "Purchase Receipt": "contact_mobile",
        "Lead": "mobile_no",
        "Project": "contact_mobile",
        "Task": "contact_mobile"
    };
    return field_map[doctype] || "contact_mobile";
}

function add_whatsapp_button(frm) {
    frm.add_custom_button(__("WhatsApp"), function() {
        trustbit_whatsapp.send_message(frm);
    }, __("Send"));
}

// Register WhatsApp button on all supported DocTypes
(function() {
    var doctypes = [
        "Sales Order", "Sales Invoice", "Purchase Order", "Purchase Invoice",
        "Quotation", "Supplier Quotation", "Material Request",
        "Delivery Note", "Purchase Receipt", "Lead", "Project", "Task"
    ];
    doctypes.forEach(function(dt) {
        frappe.ui.form.on(dt, {
            refresh: function(frm) {
                if (!frm.is_new()) {
                    add_whatsapp_button(frm);
                }
            }
        });
    });
})();
