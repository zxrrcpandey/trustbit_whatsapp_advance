# Trustbit WhatsApp Advance

Advanced WhatsApp Integration for ERPNext with Two-Way Communication

## Version
1.0.1

## Features
- Multi-provider support (360dialog, Gupshup, Twilio, Meta Direct)
- Send WhatsApp messages from any DocType
- Template-based messaging with Jinja2 support
- Automatic notifications on document events
- Two-way communication with webhook support
- Message logging and delivery status tracking
- PDF attachment support

## Installation

```bash
bench get-app https://github.com/zxrrcpandey/trustbit_whatsapp_advance.git
bench --site your-site install-app trustbit_whatsapp_advance
bench --site your-site migrate
bench build
sudo supervisorctl restart all
```

## Configuration
1. Search "WhatsApp Settings" in the awesomebar
2. Enable the integration
3. Select your provider
4. Enter API credentials
5. Save

## License
MIT
