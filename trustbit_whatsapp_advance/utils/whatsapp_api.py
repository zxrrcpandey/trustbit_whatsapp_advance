import frappe
import requests
import json

class WhatsAppAPI:
    """WhatsApp API wrapper for multiple providers"""
    
    def __init__(self):
        self.settings = frappe.get_single("WhatsApp Settings")
        self.provider = self.settings.provider
        self.api_key = self.settings.get_password("api_key")
        self.phone_number_id = self.settings.phone_number_id
        self.business_account_id = self.settings.business_account_id
    
    def send_message(self, recipient, message, media_url=None):
        """Send a WhatsApp message"""
        if not self.settings.enabled:
            return {"success": False, "error": "WhatsApp integration is disabled"}
        
        # Format recipient phone number
        recipient = self.format_phone_number(recipient)
        
        if self.provider == "360dialog":
            return self._send_360dialog(recipient, message, media_url)
        elif self.provider == "Gupshup":
            return self._send_gupshup(recipient, message, media_url)
        elif self.provider == "Twilio":
            return self._send_twilio(recipient, message, media_url)
        elif self.provider == "Meta Direct":
            return self._send_meta(recipient, message, media_url)
        else:
            return {"success": False, "error": f"Unknown provider: {self.provider}"}
    
    def format_phone_number(self, phone):
        """Format phone number with country code"""
        phone = str(phone).strip()
        phone = ''.join(filter(str.isdigit, phone))
        
        if not phone.startswith(self.settings.default_country_code):
            if phone.startswith("0"):
                phone = phone[1:]
            phone = self.settings.default_country_code + phone
        
        return phone
    
    def _send_360dialog(self, recipient, message, media_url=None):
        """Send via 360dialog"""
        url = "https://waba.360dialog.io/v1/messages"
        headers = {
            "D360-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message}
        }
        
        if media_url:
            payload["type"] = "document"
            payload["document"] = {"link": media_url}
            del payload["text"]
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Unknown error"),
                    "response": result
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_gupshup(self, recipient, message, media_url=None):
        """Send via Gupshup"""
        url = "https://api.gupshup.io/sm/api/v1/msg"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        payload = {
            "channel": "whatsapp",
            "source": self.phone_number_id,
            "destination": recipient,
            "message": json.dumps({"type": "text", "text": message}),
            "src.name": self.business_account_id or "default"
        }
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            result = response.json()
            
            if result.get("status") == "submitted":
                return {
                    "success": True,
                    "message_id": result.get("messageId"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "response": result
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_twilio(self, recipient, message, media_url=None):
        """Send via Twilio"""
        from requests.auth import HTTPBasicAuth
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.business_account_id}/Messages.json"
        
        payload = {
            "From": f"whatsapp:+{self.phone_number_id}",
            "To": f"whatsapp:+{recipient}",
            "Body": message
        }
        
        if media_url:
            payload["MediaUrl"] = media_url
        
        try:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(self.business_account_id, self.api_key),
                data=payload,
                timeout=30
            )
            result = response.json()
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message_id": result.get("sid"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "response": result
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_meta(self, recipient, message, media_url=None):
        """Send via Meta Direct (Cloud API)"""
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message}
        }
        
        if media_url:
            payload["type"] = "document"
            payload["document"] = {"link": media_url}
            del payload["text"]
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Unknown error"),
                    "response": result
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

def get_api():
    """Get WhatsApp API instance"""
    return WhatsAppAPI()
