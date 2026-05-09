import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("DISCORD_TOKEN")
    PREFIX = "!"
    
    # SpiderMC Branding
    SERVER_NAME = "SpiderMC"
    COLOR_PRIMARY = 0xFF0000  # Red (matches your logo)
    COLOR_SECONDARY = 0x000000  # Black
    LOGO_URL = "https://your-logo-url.com/spidermc_logo.png"  # Replace with your logo URL
    
    # Ticket Types
    TICKET_TYPES = {
        "general": {
            "label": "🎫 General Support",
            "description": "Get help with general inquiries",
            "emoji": "🎫",
            "color": 0x3498db
        },
        "purchase": {
            "label": "🛒 Purchase Support",
            "description": "Help with store purchases and payments",
            "emoji": "🛒",
            "color": 0x2ecc71
        },
        "report": {
            "label": "🚫 Player Report",
            "description": "Report a player for rule breaking",
            "emoji": "🚫",
            "color": 0xe74c3c
        },
        "bug": {
            "label": "🐛 Bug Report",
            "description": "Report bugs and technical issues",
            "emoji": "🐛",
            "color": 0xf39c12
        }
    }