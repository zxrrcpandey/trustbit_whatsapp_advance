// WhatsApp Integration for ERPNext
frappe.provide("trustbit_whatsapp");

trustbit_whatsapp.send_message = function(frm) {
    // Get recipient field based on doctype
    let recipient_field = get_recipient_field(frm.doctype);
    let recipient = frm.doc[recipient_field];
    
    if (!recipient) {
        frappe.msgprint(__("No phone number found in {0}", [recipient_field]));
        return;
    }
    
    // Show dialog
    let d = new frappe.ui.Dialog({
        title: __("Send WhatsApp Message"),
        fields: [
            {
                fieldname: "recipient",
                fieldtype: "Data",
                label: __("Recipient"),
                default: recipient,
                reqd: 1
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
            frappe.call({
                method: "trustbit_whatsapp_advance.api.whatsapp.send_message",
                args: {
                    recipient: values.recipient,
                    message: values.message,
                    reference_doctype: frm.doctype,
                    reference_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__("Message sent successfully!"));
                        d.hide();
                    } else {
                        frappe.msgprint(__("Failed to send message. Please try again."));
                    }
                }
            });
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
                        // Render template with current doc
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
