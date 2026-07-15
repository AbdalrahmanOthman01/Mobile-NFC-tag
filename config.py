import os
from pathlib import Path
from cryptography.fernet import Fernet
from kivy.utils import platform

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DB_PATH = DATABASE_DIR / "nfc_vault.db"
KEY_PATH = DATABASE_DIR / ".vault.key"

# Ensure window size is mobile-friendly on desktop platforms
if platform not in ("android", "ios"):
    from kivy.config import Config
    Config.set("graphics", "width", "360")
    Config.set("graphics", "height", "640")
    Config.set("graphics", "resizable", "0")

# Security: Load or generate encryption key
def load_or_create_key() -> bytes:
    """Loads the encryption key from the local environment/file or generates a new one.
    In production Android, this key should be managed inside the Android Keystore.
    For this cross-platform implementation, we use a protected local key file.
    """
    if os.getenv("NFC_VAULT_KEY"):
        return os.getenv("NFC_VAULT_KEY").encode()
    
    if KEY_PATH.exists():
        with open(KEY_PATH, "rb") as key_file:
            return key_file.read()
            
    # Generate new key
    new_key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as key_file:
        key_file.write(new_key)
    return new_key

# Global Configuration Values
APP_NAME = "NFC Vault & Badge"
VERSION = "1.0.0"
ENCRYPTION_KEY = load_or_create_key()

# UI Theme Tokens
THEME_PRIMARY = "Purple"
THEME_ACCENT = "Amber"
THEME_STYLE = "Dark"  # Modern Material 3 looks stunning in Dark Mode by default

# HCE Configuration
HCE_AID = "F0010203040506"  # Custom Application ID for card emulation
