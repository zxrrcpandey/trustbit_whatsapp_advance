import frappe
import os
import json

logger = frappe.logger("whatsapp", allow_site=True)


def after_install():
    """Setup after app installation."""
    logger.info("Trustbit WhatsApp Advance - Starting installation...")

    create_module_def()
    sync_doctypes()

    logger.info("Trustbit WhatsApp Advance installed successfully!")


def create_module_def():
    """Create the Module Def for this app."""
    try:
        if not frappe.db.exists("Module Def", "Trustbit WhatsApp"):
            module_def = frappe.new_doc("Module Def")
            module_def.module_name = "Trustbit WhatsApp"
            module_def.app_name = "trustbit_whatsapp_advance"
            module_def.flags.ignore_mandatory = True
            module_def.flags.ignore_permissions = True
            module_def.insert()
            frappe.db.commit()
            logger.info("Created Module Def: Trustbit WhatsApp")
        else:
            logger.info("Module Def already exists")
    except Exception as e:
        logger.warning(f"Module Def note: {e}")


def sync_doctypes():
    """Sync all DocTypes from JSON files."""
    app_path = frappe.get_app_path("trustbit_whatsapp_advance")
    doctype_path = os.path.join(app_path, "trustbit_whatsapp", "doctype")

    if not os.path.exists(doctype_path):
        logger.warning(f"DocType path not found: {doctype_path}")
        return

    doctypes_to_sync = [
        "whatsapp_settings",
        "whatsapp_template",
        "whatsapp_message_log",
        "whatsapp_notification_rule",
    ]

    for doctype_folder in doctypes_to_sync:
        json_path = os.path.join(doctype_path, doctype_folder, f"{doctype_folder}.json")
        if os.path.exists(json_path):
            try:
                sync_doctype_from_json(json_path)
            except Exception as e:
                logger.warning(f"Could not sync {doctype_folder}: {e}")
        else:
            logger.warning(f"JSON not found: {json_path}")


def sync_doctype_from_json(json_path):
    """Create or update a DocType from its JSON file."""
    with open(json_path, "r") as f:
        doctype_data = json.load(f)

    doctype_name = doctype_data.get("name")
    if not doctype_name:
        return

    if frappe.db.exists("DocType", doctype_name):
        logger.info(f"DocType already exists: {doctype_name}")
        return

    doc = frappe.new_doc("DocType")

    skip_keys = {"doctype", "name", "__islocal"}
    for key, value in doctype_data.items():
        if key not in skip_keys and hasattr(doc, key):
            setattr(doc, key, value)

    doc.name = doctype_name
    doc.flags.ignore_mandatory = True
    doc.flags.ignore_permissions = True

    try:
        doc.insert()
        frappe.db.commit()
        logger.info(f"Created DocType: {doctype_name}")
    except frappe.DuplicateEntryError:
        logger.info(f"DocType already exists: {doctype_name}")
    except Exception as e:
        logger.error(f"Error creating {doctype_name}: {e}")


def force_sync():
    """Force sync all DocTypes.

    Call via: bench execute trustbit_whatsapp_advance.setup.force_sync
    """
    create_module_def()
    sync_doctypes()
    frappe.db.commit()
    logger.info("Force sync completed!")
