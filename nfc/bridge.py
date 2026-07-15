import logging
from kivy.utils import platform

logger = logging.getLogger(__name__)

class NFCBridge:
    def __init__(self):
        self.on_tag_scanned = None  # Callback signature: fn(tag_info: dict)
        self.on_tag_written = None  # Callback signature: fn(success: bool, message: str)
        self.on_status_changed = None  # Callback signature: fn(status: str)
        
        # Load the appropriate implementation
        if platform == "android":
            from nfc.android_nfc import AndroidNFC
            self.impl = AndroidNFC(self)
            logger.info("NFC Bridge initialized with native Android implementation.")
        else:
            from nfc.mock_nfc import MockNFC
            self.impl = MockNFC(self)
            logger.info("NFC Bridge initialized with desktop Mock implementation.")

    def start_scan(self):
        """Activates NFC tag scanning."""
        try:
            self.impl.start_scan()
        except Exception as e:
            logger.error(f"Error starting NFC scan: {e}")
            if self.on_status_changed:
                self.on_status_changed(f"Scan Error: {str(e)}")

    def stop_scan(self):
        """Deactivates NFC tag scanning."""
        try:
            self.impl.stop_scan()
        except Exception as e:
            logger.error(f"Error stopping NFC scan: {e}")

    def prepare_write(self, payload_type: str, payload_data: str):
        """Prepares NFC for writing a specific record on the next tap."""
        try:
            self.impl.prepare_write(payload_type, payload_data)
        except Exception as e:
            logger.error(f"Error preparing NFC write: {e}")
            if self.on_tag_written:
                self.on_tag_written(False, f"Write Init Error: {str(e)}")

    def cancel_write(self):
        """Cancels any pending write state."""
        try:
            self.impl.cancel_write()
        except Exception as e:
            logger.error(f"Error cancelling write state: {e}")

    def set_hce_state(self, enabled: bool):
        """Enables or disables Host Card Emulation (HCE) badge mode."""
        try:
            self.impl.set_hce_state(enabled)
        except Exception as e:
            logger.error(f"Error setting HCE state: {e}")
            if self.on_status_changed:
                self.on_status_changed(f"HCE Error: {str(e)}")
