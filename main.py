import logging
from kivymd.app import MDApp
from config import APP_NAME, THEME_PRIMARY, THEME_ACCENT, THEME_STYLE
from database.connection import initialize_db
from nfc.bridge import NFCBridge
from ui.app_layout import AppLayout

# Setup basic logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

class NFCVaultApp(MDApp):
    """The core application class that boots up systems and configs."""
    def build(self):
        logger.info("Initializing database migrations...")
        try:
            initialize_db()
        except Exception as e:
            logger.critical(f"Failed to bootstrap database: {e}")
            raise e

        # Configure App theme properties
        self.title = APP_NAME
        self.theme_cls.primary_palette = THEME_PRIMARY
        self.theme_cls.accent_palette = THEME_ACCENT
        self.theme_cls.theme_style = THEME_STYLE

        logger.info("Initializing hardware abstraction bridge...")
        self.bridge = NFCBridge()

        logger.info("Assembling root user interface...")
        self.root_layout = AppLayout(self.bridge)
        return self.root_layout

    def on_stop(self):
        """Clean up resources on shutdown."""
        logger.info("Application stopping. Disabling NFC scan binds.")
        if hasattr(self, "bridge") and self.bridge:
            self.bridge.stop_scan()
            self.bridge.cancel_write()

if __name__ == "__main__":
    # Boot the application
    NFCVaultApp().run()
