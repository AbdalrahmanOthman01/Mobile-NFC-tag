import logging
from pathlib import Path
from kivy.metrics import dp
from kivy.utils import platform
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.snackbar import Snackbar
from config import THEME_PRIMARY

logger = logging.getLogger(__name__)

class NFCInfoCard(MDCard):
    """A premium card widget to present diagnostic read metrics of scanned NFC tags."""
    def __init__(self, tag_info, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = dp(16)
        self.spacing = dp(8)
        self.radius = [dp(16)]
        self.elevation = 2
        
        # Color matching
        self.line_color = (0.2, 0.2, 0.2, 0.5)
        self.line_width = dp(1)

        payload = tag_info.get("payload", "")
        if payload.startswith("VCARD:"):
            self.height = dp(240)
            self._build_vcard_ui(tag_info)
        elif payload.startswith("FILE:"):
            self.height = dp(260)
            self._build_file_ui(tag_info)
        else:
            self.height = dp(200)
            self._build_generic_ui(tag_info)

    def _build_generic_ui(self, tag_info):
        # Title / Header
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(8))
        header.add_widget(MDIconButton(icon="nfc", theme_text_color="Custom", text_color=(0.5, 0.3, 0.8, 1)))
        header.add_widget(MDLabel(
            text=tag_info.get("type", "Unknown HF Tag"),
            font_style="H6",
            bold=True,
            theme_text_color="Primary"
        ))
        self.add_widget(header)

        # UID Field
        uid_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(25))
        uid_layout.add_widget(MDLabel(text="Unique ID (UID):", bold=True, size_hint_x=0.4))
        uid_layout.add_widget(MDLabel(text=tag_info.get("uid", "N/A"), theme_text_color="Secondary"))
        self.add_widget(uid_layout)

        # Tech List Field
        techs = tag_info.get("tech_list", [])
        techs_str = ", ".join(techs) if isinstance(techs, list) else str(techs)
        tech_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(25))
        tech_layout.add_widget(MDLabel(text="Technologies:", bold=True, size_hint_x=0.4))
        tech_layout.add_widget(MDLabel(text=techs_str, theme_text_color="Hint", shortem=True))
        self.add_widget(tech_layout)

        # Payload Field
        self.add_widget(MDLabel(text="Payload Data:", bold=True, size_hint_y=None, height=dp(20)))
        payload_text = tag_info.get("payload", "")
        if not payload_text:
            payload_text = "[Empty / Formatted NDEF]"
        self.add_widget(MDLabel(
            text=payload_text,
            theme_text_color="Secondary",
            valign="top"
        ))

    def _build_vcard_ui(self, tag_info):
        from nfc.parsers import parse_vcard
        raw_vcard = tag_info.get("payload", "").replace("VCARD:", "", 1)
        self.parsed_data = parse_vcard(raw_vcard)

        # Header
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(8))
        header.add_widget(MDIconButton(icon="account-box-outline", theme_text_color="Custom", text_color=(0.55, 0.35, 0.85, 1)))
        
        full_name = f"{self.parsed_data['first_name']} {self.parsed_data['last_name']}".strip()
        header.add_widget(MDLabel(
            text=full_name or "Contact Card",
            font_style="H6",
            bold=True,
            theme_text_color="Primary"
        ))
        self.add_widget(header)

        # Detail Rows
        details_box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        
        if self.parsed_data["phone"]:
            row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
            row.add_widget(MDLabel(text="Phone:", bold=True, size_hint_x=0.3))
            row.add_widget(MDLabel(text=self.parsed_data["phone"], theme_text_color="Secondary"))
            details_box.add_widget(row)
            
        if self.parsed_data["email"]:
            row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
            row.add_widget(MDLabel(text="Email:", bold=True, size_hint_x=0.3))
            row.add_widget(MDLabel(text=self.parsed_data["email"], theme_text_color="Secondary"))
            details_box.add_widget(row)
            
        if self.parsed_data["company"]:
            row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
            row.add_widget(MDLabel(text="Company:", bold=True, size_hint_x=0.3))
            row.add_widget(MDLabel(text=self.parsed_data["company"], theme_text_color="Secondary"))
            details_box.add_widget(row)
            
        if self.parsed_data["website"]:
            row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
            row.add_widget(MDLabel(text="Website:", bold=True, size_hint_x=0.3))
            row.add_widget(MDLabel(text=self.parsed_data["website"], theme_text_color="Secondary"))
            details_box.add_widget(row)

        self.add_widget(details_box)

        # Action Button
        btn = MDRaisedButton(
            text="ADD TO CONTACTS",
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
            on_release=self._add_to_contacts
        )
        self.add_widget(btn)

    def _build_file_ui(self, tag_info):
        from nfc.parsers import parse_file_payload
        raw_file = tag_info.get("payload", "").replace("FILE:", "", 1)
        self.parsed_data = parse_file_payload(raw_file)

        # Header
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(8))
        header.add_widget(MDIconButton(icon="file-document-outline", theme_text_color="Custom", text_color=(0.1, 0.8, 0.6, 1)))
        header.add_widget(MDLabel(
            text=self.parsed_data["name"],
            font_style="H6",
            bold=True,
            theme_text_color="Primary"
        ))
        self.add_widget(header)

        # Detail Rows
        details_box = MDBoxLayout(orientation="vertical", spacing=dp(2))
        
        size_str = f"{len(self.parsed_data['raw_bytes'])} bytes"
        row1 = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        row1.add_widget(MDLabel(text="File Size:", bold=True, size_hint_x=0.3))
        row1.add_widget(MDLabel(text=size_str, theme_text_color="Secondary"))
        details_box.add_widget(row1)

        row2 = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        row2.add_widget(MDLabel(text="Mime Type:", bold=True, size_hint_x=0.3))
        row2.add_widget(MDLabel(text=self.parsed_data["mime"], theme_text_color="Secondary"))
        details_box.add_widget(row2)

        # Preview Label
        details_box.add_widget(MDLabel(text="Content Preview:", bold=True, size_hint_y=None, height=dp(20)))
        preview_text = self.parsed_data["content"]
        if len(preview_text) > 80:
            preview_text = preview_text[:80] + "..."
        details_box.add_widget(MDLabel(
            text=preview_text or "[Binary Data]",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(35)
        ))

        self.add_widget(details_box)

        # Action Button
        btn = MDRaisedButton(
            text="DOWNLOAD FILE",
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
            on_release=self._download_file
        )
        self.add_widget(btn)

    def _add_to_contacts(self, instance):
        first_name = self.parsed_data.get("first_name", "")
        last_name = self.parsed_data.get("last_name", "")
        phone = self.parsed_data.get("phone", "")
        email = self.parsed_data.get("email", "")
        company = self.parsed_data.get("company", "")
        
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                ContactsContract = autoclass("android.provider.ContactsContract")
                intent = Intent(Intent.ACTION_INSERT)
                intent.setType(ContactsContract.RawContacts.CONTENT_TYPE)
                intent.putExtra(ContactsContract.Intents.Insert.NAME, f"{first_name} {last_name}".strip())
                if phone:
                    intent.putExtra(ContactsContract.Intents.Insert.PHONE, phone)
                if email:
                    intent.putExtra(ContactsContract.Intents.Insert.EMAIL, email)
                if company:
                    intent.putExtra(ContactsContract.Intents.Insert.COMPANY, company)
                
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                PythonActivity.mActivity.startActivity(intent)
            except Exception as e:
                logger.error(f"Android JNI Contacts Error: {e}")
                Snackbar(text=f"Failed to launch Contacts app: {e}", duration=2.5).open()
        else:
            logger.info(f"Mock Contact: {first_name} {last_name} Phone: {phone}")
            Snackbar(
                text=f"Simulated: Added '{first_name} {last_name}' to address book.",
                bg_color=(0.1, 0.6, 0.4, 1),
                duration=2.5
            ).open()

    def _download_file(self, instance):
        filename = self.parsed_data.get("name", "downloaded_file.bin")
        raw_bytes = self.parsed_data.get("raw_bytes", b"")
        
        saved_path = ""
        if platform == "android":
            try:
                from jnius import autoclass
                Environment = autoclass("android.os.Environment")
                downloads_dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
                dest_path = Path(downloads_dir) / filename
                dest_path.write_bytes(raw_bytes)
                saved_path = str(dest_path)
            except Exception as e:
                logger.error(f"Android External Storage Error: {e}")
                from config import DATABASE_DIR
                dest_path = DATABASE_DIR / filename
                dest_path.write_bytes(raw_bytes)
                saved_path = str(dest_path)
        else:
            downloads_dir = Path.home() / "Downloads"
            if not downloads_dir.exists():
                downloads_dir = Path(".")
            dest_path = downloads_dir / filename
            dest_path.write_bytes(raw_bytes)
            saved_path = str(dest_path)

        Snackbar(
            text=f"Saved file to: {Path(saved_path).name}",
            bg_color=(0.1, 0.6, 0.4, 1),
            duration=3.0
        ).open()


class VaultTagCard(MDCard):
    """A card used in the vault list representation of encrypted scanned tags."""
    def __init__(self, tag, on_delete, on_emulate, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(88)
        self.padding = dp(12)
        self.spacing = dp(12)
        self.radius = [dp(16)]
        self.elevation = 1
        
        # Decide icon based on contents
        payload = tag.get("payload", "")
        if payload.startswith("VCARD:"):
            icon = "account-box-outline"
        elif payload.startswith("FILE:"):
            icon = "file-document-outline"
        elif "wifi:" in payload.lower():
            icon = "wifi"
        elif "url:" in payload.lower() or "http" in payload.lower():
            icon = "link"
        elif "sector" in payload.lower() or "key" in payload.lower() or "pass" in payload.lower():
            icon = "key-wireless"
        else:
            icon = "credit-card-wireless"

        # Left Icon
        icon_box = MDBoxLayout(
            orientation="vertical",
            size_hint_x=None,
            width=dp(48),
            pos_hint={"center_y": 0.5}
        )
        icon_btn = MDIconButton(
            icon=icon,
            user_font_size="28sp",
            theme_text_color="Custom",
            text_color=(0.6, 0.4, 0.9, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        icon_box.add_widget(icon_btn)
        self.add_widget(icon_box)

        # Middle Details
        details = MDBoxLayout(orientation="vertical", spacing=dp(4))
        details.add_widget(MDLabel(
            text=tag.get("name", "Unnamed Tag"),
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Primary"
        ))
        details.add_widget(MDLabel(
            text=f"UID: {tag.get('uid', '')} | Type: {tag.get('tag_type', '')}",
            font_style="Caption",
            theme_text_color="Secondary"
        ))
        self.add_widget(details)

        # Right Action Buttons
        actions = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=None,
            width=dp(96),
            pos_hint={"center_y": 0.5},
            spacing=dp(4)
        )
        
        emul_btn = MDIconButton(
            icon="remote",
            tooltip="Emulate Badge",
            on_release=lambda x: on_emulate(tag)
        )
        delete_btn = MDIconButton(
            icon="delete-outline",
            theme_text_color="Custom",
            text_color=(0.9, 0.3, 0.3, 1),
            tooltip="Delete",
            on_release=lambda x: on_delete(tag)
        )
        
        actions.add_widget(emul_btn)
        actions.add_widget(delete_btn)
        self.add_widget(actions)
