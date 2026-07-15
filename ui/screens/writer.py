import logging
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.utils import platform

logger = logging.getLogger(__name__)

class WriterScreen(MDScreen):
    def __init__(self, bridge, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge
        self.name = "writer"
        
        # Write state variables
        self.selected_format = "URL"  # URL, TEXT, WIFI, VCARD, or FILE
        self.format_menu = None

        self._build_ui()

    def _build_ui(self):
        self.main_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(16)
        )

        # Header title
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        header.add_widget(MDLabel(
            text="NFC Tag Writer",
            font_style="H5",
            bold=True
        ))
        self.main_layout.add_widget(header)

        # Format Selector Button
        self.format_btn = MDRaisedButton(
            text="Format: Web URL",
            pos_hint={"center_x": 0.5},
            on_release=self._open_format_menu
        )
        self.main_layout.add_widget(self.format_btn)

        # Scrollview wrapper for the dynamic forms
        self.scroll = ScrollView(size_hint=(1, 1))
        
        # Form Inputs Container
        self.form_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None
        )
        self.form_box.bind(minimum_height=self.form_box.setter('height'))
        
        self.scroll.add_widget(self.form_box)
        self.main_layout.add_widget(self.scroll)
        
        # Initialize forms
        self._load_url_form()

        # Write Trigger Button
        self.btn_write = MDRaisedButton(
            text="ARM WRITER",
            size_hint_x=0.6,
            pos_hint={"center_x": 0.5},
            on_release=self._arm_nfc_writer
        )
        self.main_layout.add_widget(self.btn_write)

        # Formatting Dropdown Menu setup
        self.format_menu = MDDropdownMenu(
            caller=self.format_btn,
            items=[
                {
                    "viewclass": "OneLineListItem",
                    "text": "Web URL / Deep Link",
                    "on_release": lambda: self._set_format("URL"),
                },
                {
                    "viewclass": "OneLineListItem",
                    "text": "Plain Text Message",
                    "on_release": lambda: self._set_format("TEXT"),
                },
                {
                    "viewclass": "OneLineListItem",
                    "text": "Wi-Fi Config (Tap to Join)",
                    "on_release": lambda: self._set_format("WIFI"),
                },
                {
                    "viewclass": "OneLineListItem",
                    "text": "vCard (Contact Card)",
                    "on_release": lambda: self._set_format("VCARD"),
                },
                {
                    "viewclass": "OneLineListItem",
                    "text": "File Transfer",
                    "on_release": lambda: self._set_format("FILE"),
                },
            ],
            width_mult=4,
        )

        self.add_widget(self.main_layout)

    def _open_format_menu(self, button):
        self.format_menu.open()

    def _set_format(self, fmt_code: str):
        self.format_menu.dismiss()
        self.selected_format = fmt_code
        
        # Clear forms
        self.form_box.clear_widgets()

        if fmt_code == "URL":
            self.format_btn.text = "Format: Web URL"
            self._load_url_form()
        elif fmt_code == "TEXT":
            self.format_btn.text = "Format: Plain Text"
            self._load_text_form()
        elif fmt_code == "WIFI":
            self.format_btn.text = "Format: Wi-Fi Config"
            self._load_wifi_form()
        elif fmt_code == "VCARD":
            self.format_btn.text = "Format: Contact Card"
            self._load_vcard_form()
        elif fmt_code == "FILE":
            self.format_btn.text = "Format: File Transfer"
            self._load_file_form()

    # Form UI loaders
    def _load_url_form(self):
        self.txt_url = MDTextField(
            text="https://",
            hint_text="Destination URL",
            helper_text="Must include protocol (http:// or https://)",
            helper_text_mode="on_focus"
        )
        self.form_box.add_widget(self.txt_url)

    def _load_text_form(self):
        self.txt_text = MDTextField(
            hint_text="Secure Plain Text",
            helper_text="Enter tag content details",
            helper_text_mode="on_focus",
            multiline=True,
            max_height="120dp"
        )
        self.form_box.add_widget(self.txt_text)

    def _load_wifi_form(self):
        self.txt_ssid = MDTextField(
            hint_text="Network SSID (Name)",
            helper_text="Enter Wi-Fi name",
            helper_text_mode="on_focus"
        )
        self.txt_password = MDTextField(
            hint_text="Network Password",
            helper_text="Leave blank if unsecured network",
            helper_text_mode="on_focus",
            password=True
        )
        self.form_box.add_widget(self.txt_ssid)
        self.form_box.add_widget(self.txt_password)

    def _load_vcard_form(self):
        self.txt_first_name = MDTextField(hint_text="First Name", size_hint_y=None, height=dp(40))
        self.txt_last_name = MDTextField(hint_text="Last Name", size_hint_y=None, height=dp(40))
        self.txt_phone = MDTextField(hint_text="Phone Number", size_hint_y=None, height=dp(40))
        self.txt_email = MDTextField(hint_text="Email Address", size_hint_y=None, height=dp(40))
        self.txt_company = MDTextField(hint_text="Company / Org", size_hint_y=None, height=dp(40))
        self.txt_website = MDTextField(text="https://", hint_text="Website (Optional)", size_hint_y=None, height=dp(40))
        
        self.form_box.add_widget(self.txt_first_name)
        self.form_box.add_widget(self.txt_last_name)
        self.form_box.add_widget(self.txt_phone)
        self.form_box.add_widget(self.txt_email)
        self.form_box.add_widget(self.txt_company)
        self.form_box.add_widget(self.txt_website)

    def _load_file_form(self):
        self.txt_filename = MDTextField(hint_text="Filename (e.g. notes.txt)", size_hint_y=None, height=dp(40))
        self.txt_file_mime = MDTextField(text="text/plain", hint_text="MIME Type", size_hint_y=None, height=dp(40))
        self.txt_file_content = MDTextField(
            hint_text="File Contents",
            helper_text="Warning: NFC tags have very limited capacity (typically < 800 bytes).",
            helper_text_mode="on_focus",
            multiline=True,
            max_height="120dp"
        )
        self.form_box.add_widget(self.txt_filename)
        self.form_box.add_widget(self.txt_file_mime)
        self.form_box.add_widget(self.txt_file_content)

    # Core write operations
    def _get_payload_data(self) -> str:
        """Serializes form inputs into clean tag formats."""
        if self.selected_format == "URL":
            url = self.txt_url.text.strip()
            if not url or url in ("http://", "https://"):
                return ""
            return url
        elif self.selected_format == "TEXT":
            return self.txt_text.text.strip()
        elif self.selected_format == "WIFI":
            ssid = self.txt_ssid.text.strip()
            password = self.txt_password.text.strip()
            if not ssid:
                return ""
            return f"WIFI:S:{ssid};T:WPA;P:{password};;"
        elif self.selected_format == "VCARD":
            from nfc.parsers import make_vcard
            fn = self.txt_first_name.text.strip()
            ln = self.txt_last_name.text.strip()
            phone = self.txt_phone.text.strip()
            email = self.txt_email.text.strip()
            company = self.txt_company.text.strip()
            web = self.txt_website.text.strip()
            
            if not fn and not ln:
                return ""
            return make_vcard(fn, ln, phone, email, company, web)
        elif self.selected_format == "FILE":
            from nfc.parsers import make_file_payload
            filename = self.txt_filename.text.strip()
            mime = self.txt_file_mime.text.strip()
            content = self.txt_file_content.text.strip()
            
            if not filename or not content:
                return ""
            return make_file_payload(filename, mime, content)
        return ""

    def _arm_nfc_writer(self, button):
        payload = self._get_payload_data()
        if not payload:
            return
            
        # Call global NFC bottom sheet in write mode
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if hasattr(app, "root") and app.root:
            app.root.show_nfc_sheet(
                mode="write",
                payload_type=self.selected_format,
                payload_data=payload,
                on_tag_processed=self.on_tag_written
            )

    def on_tag_written(self, result: dict):
        """Callback triggered on successful completion of nfc write operation."""
        # Clean fields
        self._set_format(self.selected_format)
