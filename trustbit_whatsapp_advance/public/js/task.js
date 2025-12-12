frappe.ui.form.on("Task", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("WhatsApp"), function() {
                trustbit_whatsapp.send_message(frm);
            }, __("Send"));
        }
    }
});
