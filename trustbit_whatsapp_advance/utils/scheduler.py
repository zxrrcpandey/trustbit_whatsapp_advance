import frappe
import json
from frappe.utils import add_days, add_minutes, nowdate, now_datetime


def process_pending_messages():
    """Retry sending messages stuck in Pending status.

    Runs every 5 minutes via scheduler.  Picks up messages that have been
    Pending for more than 2 minutes (to avoid racing with the initial send)
    and retries them up to 3 times.
    """
    try:
        settings = frappe.get_single("WhatsApp Settings")
        if not settings.enabled:
            return

        cutoff = add_minutes(now_datetime(), -2)

        pending_logs = frappe.get_all(
            "WhatsApp Message Log",
            filters={
                "status": "Pending",
                "creation": ["<", cutoff],
            },
            fields=["name", "recipient", "message", "reference_doctype", "reference_name"],
            limit=50,
            order_by="creation asc",
        )

        if not pending_logs:
            return

        from trustbit_whatsapp_advance.utils.whatsapp_api import get_api

        api = get_api()

        for entry in pending_logs:
            try:
                log = frappe.get_doc("WhatsApp Message Log", entry.name)

                # Count previous retries (stored in provider_response)
                retry_count = 0
                if log.provider_response:
                    try:
                        resp = json.loads(log.provider_response)
                        retry_count = resp.get("_retry_count", 0)
                    except (json.JSONDecodeError, TypeError):
                        pass

                if retry_count >= 3:
                    log.status = "Failed"
                    log.error_message = "Max retries (3) exceeded"
                    log.save()
                    frappe.db.commit()
                    continue

                result = api.send_message(log.recipient, log.message)

                if result.get("success"):
                    log.status = "Sent"
                    log.message_id = result.get("message_id")
                else:
                    log.error_message = str(result.get("error", "Unknown error"))[:2000]

                # Track retry count
                try:
                    resp_data = result.get("response", {})
                    if not isinstance(resp_data, dict):
                        resp_data = {}
                    resp_data["_retry_count"] = retry_count + 1
                    log.provider_response = json.dumps(resp_data, default=str)[:10000]
                except (TypeError, ValueError):
                    pass

                log.save()
                frappe.db.commit()

            except Exception as e:
                frappe.log_error(
                    f"Error retrying message {entry.name}: {e}",
                    "WhatsApp Scheduler Error",
                )
                frappe.db.rollback()

    except Exception as e:
        frappe.log_error(f"process_pending_messages error: {e}", "WhatsApp Scheduler Error")


def update_message_status():
    """Mark old Sent messages as potentially lost.

    Runs hourly. Messages that have been in 'Sent' status for over 24 hours
    without a webhook delivery/read update are flagged.
    """
    try:
        settings = frappe.get_single("WhatsApp Settings")
        if not settings.enabled:
            return

        cutoff = add_days(now_datetime(), -1)

        stale_logs = frappe.get_all(
            "WhatsApp Message Log",
            filters={
                "status": "Sent",
                "creation": ["<", cutoff],
            },
            fields=["name"],
            limit=200,
        )

        for entry in stale_logs:
            try:
                frappe.db.set_value(
                    "WhatsApp Message Log",
                    entry.name,
                    "error_message",
                    "No delivery confirmation received within 24 hours",
                )
            except Exception:
                pass

        if stale_logs:
            frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"update_message_status error: {e}", "WhatsApp Scheduler Error")


def cleanup_old_logs():
    """Clean up old message logs beyond retention period."""
    try:
        settings = frappe.get_single("WhatsApp Settings")
        retention_days = settings.message_log_retention_days or 90

        cutoff_date = add_days(nowdate(), -retention_days)

        frappe.db.sql(
            """
            DELETE FROM `tabWhatsApp Message Log`
            WHERE creation < %s
            LIMIT 5000
            """,
            (cutoff_date,),
        )

        frappe.db.commit()
        frappe.db.set_single_value("WhatsApp Settings", "last_cleanup_date", nowdate())
    except Exception as e:
        frappe.log_error(f"WhatsApp log cleanup error: {e}", "WhatsApp Cleanup Error")
