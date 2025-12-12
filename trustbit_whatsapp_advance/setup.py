import frappe
import os
import json

def after_install():
    """Setup after app installation"""
    print("Trustbit WhatsApp Advance - Starting installation...")
    
    # Step 1: Create Module Def if not exists
    create_module_def()
    
    # Step 2: Sync DocTypes from JSON files
    sync_doctypes()
    
    print("")
    print("=" * 60)
    print("Trustbit WhatsApp Advance installed successfully!")
    print("Search 'WhatsApp Settings' in the awesomebar to configure.")
    print("=" * 60)

def create_module_def():
    """Create the Module Def for this app"""
    try:
        if not frappe.db.exists("Module Def", "Trustbit WhatsApp Advance"):
            module_def = frappe.new_doc("Module Def")
            module_def.module_name = "Trustbit WhatsApp Advance"
            module_def.app_name = "trustbit_whatsapp_advance"
            module_def.flags.ignore_mandatory = True
            module_def.insert(ignore_permissions=True)
            frappe.db.commit()
            print("✓ Created Module Def: Trustbit WhatsApp Advance")
        else:
            print("✓ Module Def already exists")
    except Exception as e:
        print(f"! Module Def note: {e}")

def sync_doctypes():
    """Sync all DocTypes from JSON files"""
    app_path = frappe.get_app_path("trustbit_whatsapp_advance")
    doctype_path = os.path.join(app_path, "doctype")
    
    if not os.path.exists(doctype_path):
        print(f"! DocType path not found: {doctype_path}")
        return
    
    # List of DocTypes to sync in order
    doctypes_to_sync = [
        "whatsapp_settings",
        "whatsapp_template", 
        "whatsapp_message_log",
        "whatsapp_notification_rule"
    ]
    
    for doctype_folder in doctypes_to_sync:
        json_path = os.path.join(doctype_path, doctype_folder, f"{doctype_folder}.json")
        if os.path.exists(json_path):
            try:
                sync_doctype_from_json(json_path)
            except Exception as e:
                print(f"! Could not sync {doctype_folder}: {e}")
        else:
            print(f"! JSON not found: {json_path}")

def sync_doctype_from_json(json_path):
    """Create or update a DocType from its JSON file"""
    with open(json_path, 'r') as f:
        doctype_data = json.load(f)
    
    doctype_name = doctype_data.get("name")
    if not doctype_name:
        return
    
    # Check if DocType already exists
    if frappe.db.exists("DocType", doctype_name):
        print(f"✓ DocType already exists: {doctype_name}")
        return
    
    # Create new DocType
    doc = frappe.new_doc("DocType")
    
    # Copy all fields from JSON
    for key, value in doctype_data.items():
        if key not in ["doctype", "name", "__islocal"]:
            if hasattr(doc, key):
                setattr(doc, key, value)
    
    doc.name = doctype_name
    doc.flags.ignore_mandatory = True
    doc.flags.ignore_permissions = True
    
    # Insert
    try:
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"✓ Created DocType: {doctype_name}")
    except frappe.DuplicateEntryError:
        print(f"✓ DocType already exists: {doctype_name}")
    except Exception as e:
        print(f"! Error creating {doctype_name}: {e}")

def force_sync():
    """Force sync all DocTypes - call via: bench execute trustbit_whatsapp_advance.setup.force_sync"""
    create_module_def()
    sync_doctypes()
    frappe.db.commit()
    print("Force sync completed!")
