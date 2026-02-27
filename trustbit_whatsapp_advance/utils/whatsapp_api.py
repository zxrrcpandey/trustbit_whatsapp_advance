import frappe
import requests
import json

# Request timeout in seconds
REQUEST_TIMEOUT = 30


class WhatsAppAPI:
    """WhatsApp API wrapper for multiple providers."""

    def __init__(self):
        self.settings = frappe.get_single("WhatsApp Settings")
        self.provider = self.settings.provider
        self.api_key = self.settings.get_password("api_key")
        self.phone_number_id = self.settings.phone_number_id
        self.business_account_id = self.settings.business_account_id

    def send_message(self, recipient, message, media_url=None):
        """Send a WhatsApp message via the configured provider."""
        if not self.settings.enabled:
            return {"success": False, "error": "WhatsApp integration is disabled"}

        if not recipient:
            return {"success": False, "error": "No recipient specified"}

        # Format recipient phone number
        recipient = self.format_phone_number(recipient)

        provider_map = {
            "360dialog": self._send_360dialog,
            "Gupshup": self._send_gupshup,
            "Twilio": self._send_twilio,
            "Meta Direct": self._send_meta,
        }

        handler = provider_map.get(self.provider)
        if not handler:
            return {"success": False, "error": f"Unknown provider: {self.provider}"}

        return handler(recipient, message, media_url)

    def format_phone_number(self, phone):
        """Format phone number with country code."""
        phone = str(phone).strip()
        phone = "".join(c for c in phone if c.isdigit())

        if not phone:
            return ""

        default_code = self.settings.default_country_code or "91"
        if not phone.startswith(default_code):
            if phone.startswith("0"):
                phone = phone[1:]
            phone = default_code + phone

        return phone

    def _make_request(self, method, url, **kwargs):
        """Central request method with explicit SSL verify and timeout."""
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        kwargs["verify"] = True

        try:
            response = getattr(requests, method)(url, **kwargs)
            return response
        except requests.exceptions.SSLError as e:
            frappe.log_error(f"SSL error calling {url}: {e}", "WhatsApp API SSL Error")
            raise
        except requests.exceptions.ConnectionError as e:
            frappe.log_error(f"Connection error calling {url}: {e}", "WhatsApp API Error")
            raise
        except requests.exceptions.Timeout as e:
            frappe.log_error(f"Timeout calling {url}: {e}", "WhatsApp API Timeout")
            raise

    def _send_360dialog(self, recipient, message, media_url=None):
        """Send via 360dialog."""
        url = "https://waba.360dialog.io/v1/messages"
        headers = {
            "D360-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message},
        }

        if media_url:
            payload["type"] = "document"
            payload["document"] = {"link": media_url}
            payload.pop("text", None)

        try:
            response = self._make_request("post", url, headers=headers, json=payload)
            result = response.json()

            if response.status_code == 200:
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "response": result,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Unknown error"),
                    "response": result,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _send_gupshup(self, recipient, message, media_url=None):
        """Send via Gupshup."""
        url = "https://api.gupshup.io/sm/api/v1/msg"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        payload = {
            "channel": "whatsapp",
            "source": self.phone_number_id,
            "destination": recipient,
            "message": json.dumps({"type": "text", "text": message}),
            "src.name": self.business_account_id or "default",
        }

        try:
            response = self._make_request("post", url, headers=headers, data=payload)
            result = response.json()

            if result.get("status") == "submitted":
                return {
                    "success": True,
                    "message_id": result.get("messageId"),
                    "response": result,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "response": result,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _send_twilio(self, recipient, message, media_url=None):
        """Send via Twilio."""
        from requests.auth import HTTPBasicAuth

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.business_account_id}/Messages.json"

        payload = {
            "From": f"whatsapp:+{self.phone_number_id}",
            "To": f"whatsapp:+{recipient}",
            "Body": message,
        }

        if media_url:
            payload["MediaUrl"] = media_url

        try:
            response = self._make_request(
                "post",
                url,
                auth=HTTPBasicAuth(self.business_account_id, self.api_key),
                data=payload,
            )
            result = response.json()

            if response.status_code in (200, 201):
                return {
                    "success": True,
                    "message_id": result.get("sid"),
                    "response": result,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "response": result,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _send_meta(self, recipient, message, media_url=None):
        """Send via Meta Direct (Cloud API)."""
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message},
        }

        if media_url:
            payload["type"] = "document"
            payload["document"] = {"link": media_url}
            payload.pop("text", None)

        try:
            response = self._make_request("post", url, headers=headers, json=payload)
            result = response.json()

            if response.status_code == 200:
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "response": result,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Unknown error"),
                    "response": result,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_api():
    """Get WhatsApp API instance."""
    return WhatsAppAPI()
