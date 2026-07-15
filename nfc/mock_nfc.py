import logging

logger = logging.getLogger(__name__)

class MockNFC:
    def __init__(self, bridge):
        self.bridge = bridge
        self.scanning = False
        self.pending_write_type = None
        self.pending_write_data = None
        self.hce_enabled = False

    def start_scan(self):
        self.scanning = True
        logger.info("Mock NFC: Started Scanning")
        if self.bridge.on_status_changed:
            self.bridge.on_status_changed("Scanning for tags...")

    def stop_scan(self):
        self.scanning = False
        logger.info("Mock NFC: Stopped Scanning")
        if self.bridge.on_status_changed:
            self.bridge.on_status_changed("Scanner ready")

    def prepare_write(self, payload_type: str, payload_data: str):
        self.pending_write_type = payload_type
        self.pending_write_data = payload_data
        logger.info(f"Mock NFC: Ready to write {payload_type} data: {payload_data}")
        if self.bridge.on_status_changed:
            self.bridge.on_status_changed(f"Ready to write: {payload_type}")

    def cancel_write(self):
        self.pending_write_type = None
        self.pending_write_data = None
        logger.info("Mock NFC: Write cancelled")
        if self.bridge.on_status_changed:
            self.bridge.on_status_changed("Write cancelled")

    def set_hce_state(self, enabled: bool):
        self.hce_enabled = enabled
        status = "HCE Badge Active" if enabled else "HCE Badge Inactive"
        logger.info(f"Mock NFC: HCE State set to {enabled}")
        if self.bridge.on_status_changed:
            self.bridge.on_status_changed(status)

    def trigger_mock_tag(self, uid: str, tag_type: str, payload: str):
        """Simulates touching an NFC tag to the phone.
        Called by desktop debug dialogs to mock hardware operations.
        """
        if not self.scanning and not self.pending_write_type:
            if self.bridge.on_status_changed:
                self.bridge.on_status_changed("Tag detected, but scanner is offline.")
            return

        if self.pending_write_type:
            # Simulate a write transaction
            write_success = True
            msg = f"Successfully wrote {self.pending_write_type} record to tag {uid}."
            
            # Log write transaction securely in database
            from database.repository import log_written_record
            log_written_record(self.pending_write_type, self.pending_write_data)
            
            # Reset write state
            self.pending_write_type = None
            self.pending_write_data = None
            
            if self.bridge.on_tag_written:
                self.bridge.on_tag_written(write_success, msg)
            if self.bridge.on_status_changed:
                self.bridge.on_status_changed("Write successful!")
        else:
            # Simulate a read scan
            tag_info = {
                "uid": uid,
                "type": tag_type,
                "payload": payload,
                "tech_list": ["NfcA", "Ndef", "MifareClassic"]
            }
            if self.bridge.on_tag_scanned:
                self.bridge.on_tag_scanned(tag_info)
            if self.bridge.on_status_changed:
                self.bridge.on_status_changed("Tag scanned successfully!")
                
    def trigger_mock_hce_handshake(self) -> str:
        """Simulates a contactless reader reading the emulated digital badge."""
        if not self.hce_enabled:
            return "HCE Emulation Disabled"
        return f"APDU Transmit: SELECT AID [F0010203040506] -> SW1_SW2 [90 00]"
