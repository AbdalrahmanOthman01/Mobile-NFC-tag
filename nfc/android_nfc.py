import logging
import threading
from kivy.clock import Clock
from kivy.utils import platform

logger = logging.getLogger(__name__)

# Only import pyjnius classes if we are actually on Android
if platform == "android":
    from jnius import autoclass, PythonJavaClass, java_method
    
    # Core Android & Kivy classes
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    NfcAdapter = autoclass("android.nfc.NfcAdapter")
    Ndef = autoclass("android.nfc.tech.Ndef")
    NdefMessage = autoclass("android.nfc.NdefMessage")
    NdefRecord = autoclass("android.nfc.NdefRecord")
    Intent = autoclass("android.content.Intent")
    ComponentName = autoclass("android.content.ComponentName")
    PackageManager = autoclass("android.content.pm.PackageManager")
    
    # Java Types
    String = autoclass("java.lang.String")
    Charset = autoclass("java.nio.charset.Charset")
    
    class NFCReaderCallback(PythonJavaClass):
        """Implements NfcAdapter.ReaderCallback to listen for tag scan events in a background thread."""
        __javainterfaces__ = ["android/nfc/NfcAdapter$ReaderCallback"]
        __javacontext__ = "app"
        
        def __init__(self, callback):
            super().__init__()
            self.callback = callback
            
        @java_method("(Landroid/nfc/Tag;)V")
        def onTagDiscovered(self, tag):
            logger.info("NFC Tag detected by Android ReaderCallback")
            self.callback(tag)
else:
    # Placeholders to prevent compilation crashes on desktop
    NFCReaderCallback = object

class AndroidNFC:
    def __init__(self, bridge):
        self.bridge = bridge
        self.activity = PythonActivity.mActivity
        self.nfc_adapter = NfcAdapter.getDefaultAdapter(self.activity)
        self.callback_impl = NFCReaderCallback(self._on_tag_discovered)
        
        # Write state variables
        self.pending_write_type = None
        self.pending_write_data = None

    def start_scan(self):
        """Register ReaderCallback with Android NfcAdapter."""
        if not self.nfc_adapter:
            self._update_status("NFC is not supported on this device.")
            return
            
        if not self.nfc_adapter.isEnabled():
            self._update_status("NFC is disabled. Please enable it in Settings.")
            return

        # Reader mode flags: SCAN NFC-A, NFC-B, NFC-F, NFC-V, and ISO-DEP
        flags = (
            NfcAdapter.FLAG_READER_NFC_A |
            NfcAdapter.FLAG_READER_NFC_B |
            NfcAdapter.FLAG_READER_NFC_F |
            NfcAdapter.FLAG_READER_NFC_V |
            NfcAdapter.FLAG_READER_NFC_BARCODE |
            NfcAdapter.FLAG_READER_NO_PLATFORM_SOUNDS  # Quiet tap
        )
        
        try:
            self.nfc_adapter.enableReaderMode(self.activity, self.callback_impl, flags, None)
            self._update_status("Scanning for tags...")
        except Exception as e:
            logger.error(f"Error registering Reader Mode: {e}")
            self._update_status(f"Failed to start scanner: {e}")

    def stop_scan(self):
        """Unregister ReaderCallback."""
        if self.nfc_adapter:
            try:
                self.nfc_adapter.disableReaderMode(self.activity)
                self._update_status("Scanner ready")
            except Exception as e:
                logger.error(f"Error disabling Reader Mode: {e}")

    def prepare_write(self, payload_type: str, payload_data: str):
        """Arms the writer. When a tag is tapped, we will attempt to write this data."""
        self.pending_write_type = payload_type
        self.pending_write_data = payload_data
        self._update_status(f"Ready to write: {payload_type}. Tap an NFC tag now.")

    def cancel_write(self):
        self.pending_write_type = None
        self.pending_write_data = None
        self._update_status("Write cancelled")

    def set_hce_state(self, enabled: bool):
        """Enables/disables the Host Card Emulation service component."""
        pm = self.activity.getPackageManager()
        # Compile class name matches our package and Java service name
        service_class_name = f"{self.activity.getPackageName()}.SecureBadgeService"
        component = ComponentName(self.activity, service_class_name)
        
        state = (
            PackageManager.COMPONENT_ENABLED_STATE_ENABLED 
            if enabled else 
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED
        )
        
        try:
            pm.setComponentEnabledSetting(component, state, PackageManager.DONT_KILL_APP)
            status_text = "HCE Badge Active" if enabled else "HCE Badge Inactive"
            self._update_status(status_text)
        except Exception as e:
            logger.error(f"Failed to set component state: {e}")
            self._update_status(f"HCE configuration failed: {e}")

    def _on_tag_discovered(self, tag):
        """Native callback handler triggered on tag tap."""
        if self.pending_write_type:
            self._write_ndef_to_tag(tag)
        else:
            self._read_ndef_from_tag(tag)

    def _read_ndef_from_tag(self, tag):
        """Extracts technical diagnostics and NDEF payloads from tag."""
        try:
            # 1. Parse UID
            uid_bytes = tag.getId()
            uid = ":".join(f"{b & 0xff:02X}" for b in uid_bytes)
            
            # 2. Get tech list
            tech_list = [t.split(".")[-1] for t in tag.getTechList()]
            tag_type = "Generic HF Tag"
            
            # Refine type based on tech list
            if "Ndef" in tech_list:
                tag_type = "NDEF Tag"
            elif "MifareClassic" in tech_list:
                tag_type = "Mifare Classic"
            elif "IsoDep" in tech_list:
                tag_type = "ISO-DEP Smart Card"

            payload_data = ""
            
            # 3. Read NDEF message details
            ndef = Ndef.get(tag)
            if ndef:
                ndef.connect()
                ndef_msg = ndef.getNdefMessage()
                if ndef_msg:
                    records = ndef_msg.getRecords()
                    parsed_records = []
                    for record in records:
                        parsed_records.append(self._parse_ndef_record(record))
                    payload_data = "\n".join(parsed_records)
                ndef.close()
            else:
                payload_data = f"No NDEF message found. Tech List: {', '.join(tech_list)}"

            # Dispatch back to UI thread
            tag_info = {
                "uid": uid,
                "type": tag_type,
                "payload": payload_data,
                "tech_list": tech_list
            }
            Clock.schedule_once(lambda dt: self._dispatch_tag_read(tag_info))
        except Exception as e:
            logger.error(f"Error parsing NFC tag read: {e}")
            self._update_status(f"Error reading tag: {e}")

    def _write_ndef_to_tag(self, tag):
        """Writes armed NDEF records to the tapped tag."""
        try:
            ndef = Ndef.get(tag)
            if not ndef:
                self._dispatch_write_result(False, "Tapped tag does not support standard NDEF formatting.")
                return

            ndef.connect()
            if not ndef.isWritable():
                self._dispatch_write_result(False, "Tapped tag is write-protected.")
                ndef.close()
                return

            # Construct NdefRecord
            record = self._build_ndef_record(self.pending_write_type, self.pending_write_data)
            if not record:
                self._dispatch_write_result(False, "Invalid NDEF records configurations.")
                ndef.close()
                return
                
            # Create message containing record
            records_arr = [record]
            # Pyjnius can construct java array
            from jnius import cast
            # In java: NdefMessage(NdefRecord[] records)
            ndef_msg = NdefMessage(records_arr)
            
            # Validate size limits
            if ndef_msg.getByteArrayLength() > ndef.getMaxSize():
                self._dispatch_write_result(False, f"Payload size exceeds tag capacity limit ({ndef.getMaxSize()} bytes).")
                ndef.close()
                return

            # Write!
            ndef.writeNdefMessage(ndef_msg)
            ndef.close()
            
            # Secure log write history
            from database.repository import log_written_record
            log_written_record(self.pending_write_type, self.pending_write_data)
            
            # Reset state and dispatch success
            msg = f"Successfully wrote {self.pending_write_type} record to tag."
            self.pending_write_type = None
            self.pending_write_data = None
            
            Clock.schedule_once(lambda dt: self._dispatch_write_result(True, msg))
        except Exception as e:
            logger.error(f"Error writing NFC tag: {e}")
            Clock.schedule_once(lambda dt: self._dispatch_write_result(False, f"Write failed: {e}"))

    def _parse_ndef_record(self, record) -> str:
        """Helper to convert native Android NdefRecords to human readable string."""
        tnf = record.getTnf()
        type_bytes = record.getType()
        payload_bytes = record.getPayload()
        
        # Parse URI record
        if tnf == NdefRecord.TNF_WELL_KNOWN and list(type_bytes) == list(NdefRecord.RTD_URI):
            uri = record.toUri().toString()
            return f"URI: {uri}"
            
        # Parse Text record
        elif tnf == NdefRecord.TNF_WELL_KNOWN and list(type_bytes) == list(NdefRecord.RTD_TEXT):
            # Parse lang code and text
            status_byte = payload_bytes[0]
            is_utf16 = (status_byte & 0x80) != 0
            lang_len = status_byte & 0x3F
            encoding = "utf-16" if is_utf16 else "utf-8"
            
            text_bytes = payload_bytes[1 + lang_len:]
            text = bytes(text_bytes).decode(encoding)
            return f"Text: {text}"
            
        return f"TNF {tnf}: Data Length {len(payload_bytes)} bytes"

    def _build_ndef_record(self, record_type: str, data: str) -> Optional[NdefRecord]:
        """Constructs an Android native NdefRecord based on chosen format."""
        try:
            if record_type == "URL":
                return NdefRecord.createUri(String(data))
            elif record_type == "TEXT":
                return NdefRecord.createTextRecord(String("en"), String(data))
            elif record_type == "WIFI":
                # Wifi configuration format (MIME: application/vnd.wfa.wsc)
                # For simplicity, standard Kivy applications save WiFi credentials as clean text tags
                # or URIs that mobile OS parsing engines handle automatically. We use text layout.
                return NdefRecord.createTextRecord(String("en"), String(data))
            return None
        except Exception as e:
            logger.error(f"Error building NDEF record: {e}")
            return None

    def _dispatch_tag_read(self, tag_info: dict):
        if self.bridge.on_tag_scanned:
            self.bridge.on_tag_scanned(tag_info)

    def _dispatch_write_result(self, success: bool, message: str):
        if self.bridge.on_tag_written:
            self.bridge.on_tag_written(success, message)

    def _update_status(self, status: str):
        def _set_status(dt):
            if self.bridge.on_status_changed:
                self.bridge.on_status_changed(status)
        Clock.schedule_once(_set_status)
