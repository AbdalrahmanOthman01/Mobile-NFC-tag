from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.utils import platform
from ui.components.dialogs import MockNFCScanDialog

class WriterScreen(MDScreen):
    def __init__(self, bridge, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge
        self.name = "writer"
        
        # Write state variables
        self.selected_format = "URL"  # URL, TEXT, or WIFI
        self.format_menu = None
        self.writing_active = False

        self._build_ui()
        self.bind(on_leave=self.on_screen_leave)

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

        # Form Inputs Container
        self.form_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None,
            height=dp(240)
        )
        self.main_layout.add_widget(self.form_box)
        
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

        # Desktop Debug Option
        if platform not in ("android", "ios"):
            self.debug_box = MDBoxLayout(size_hint_y=None, height=dp(50), padding=[0, dp(10)])
            self.debug_btn = MDRaisedButton(
                text="DEBUG: Trigger Tag Touch",
                md_bg_color=(0.9, 0.4, 0.1, 1),
                pos_hint={"center_x": 0.5},
                on_release=self._open_mock_dialog,
                disabled=True  # Disabled unless writer is armed
            )
            self.debug_box.add_widget(self.debug_btn)
            self.main_layout.add_widget(self.debug_box)

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
            ],
            width_mult=4,
        )

        # Overlay layer for writing state
        self.overlay_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(16),
            md_bg_color=(0.1, 0.1, 0.1, 0.95),  # Glassmorphism dark background overlay
            pos_hint={"x": 0, "y": 0},
            size_hint=(1, 1),
            opacity=0,
            disabled=True
        )
        
        self.overlay_icon = MDIconButton(
            icon="nfc-tap",
            user_font_size="90sp",
            theme_text_color="Custom",
            text_color=(0.1, 0.8, 0.6, 1),
            pos_hint={"center_x": 0.5}
        )
        self.overlay_status = MDLabel(
            text="Tap NFC Tag Now",
            font_style="H6",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        self.overlay_details = MDLabel(
            text="Waiting for contactless interaction...",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.7, 1)
        )
        
        cancel_btn = MDFlatButton(
            text="CANCEL WRITE",
            theme_text_color="Custom",
            text_color=(0.9, 0.3, 0.3, 1),
            pos_hint={"center_x": 0.5},
            on_release=self._cancel_nfc_writer
        )
        
        self.overlay_layout.add_widget(self.overlay_icon)
        self.overlay_layout.add_widget(self.overlay_status)
        self.overlay_layout.add_widget(self.overlay_details)
        self.overlay_layout.add_widget(cancel_btn)

        self.add_widget(self.main_layout)
        # Add overlay to screen layers
        self.add_widget(self.overlay_layout)

    def on_screen_leave(self, *args):
        self._cancel_nfc_writer()

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
            # Wi-Fi standard config string format
            return f"WIFI:S:{ssid};T:WPA;P:{password};;"
        return ""

    def _arm_nfc_writer(self, button):
        payload = self._get_payload_data()
        if not payload:
            return
            
        # Hook up callback hooks
        self.bridge.on_tag_written = self.on_tag_written
        self.bridge.on_status_changed = self.on_status_changed
        
        # Arm hardware
        self.bridge.prepare_write(self.selected_format, payload)
        
        # Show waiting overlay
        self.writing_active = True
        self.overlay_layout.disabled = False
        self.overlay_layout.opacity = 1
        
        if hasattr(self, "debug_btn"):
            self.debug_btn.disabled = False

    def _cancel_nfc_writer(self, *args):
        if not self.writing_active:
            return
            
        self.bridge.cancel_write()
        self.writing_active = False
        self.overlay_layout.opacity = 0
        self.overlay_layout.disabled = True
        
        if hasattr(self, "debug_btn"):
            self.debug_btn.disabled = True

    def on_status_changed(self, status: str):
        if self.writing_active:
            self.overlay_details.text = status

    def on_tag_written(self, success: bool, message: str):
        """Callback from bridge confirming transaction results."""
        if not self.writing_active:
            return
            
        if success:
            self.overlay_icon.icon = "checkbox-marked-circle"
            self.overlay_icon.text_color = (0.1, 0.8, 0.4, 1)
            self.overlay_status.text = "Write Complete"
            self.overlay_details.text = message
            
            # Dismiss overlay after a slight delay
            from kivy.clock import Clock
            Clock.schedule_once(self._finish_transaction, 1.8)
        else:
            self.overlay_icon.icon = "alert-circle"
            self.overlay_icon.text_color = (0.9, 0.3, 0.3, 1)
            self.overlay_status.text = "Transaction Failed"
            self.overlay_details.text = message

    def _finish_transaction(self, dt):
        self.writing_active = False
        self.overlay_layout.opacity = 0
        self.overlay_layout.disabled = True
        
        # Restore icons
        self.overlay_icon.icon = "nfc-tap"
        self.overlay_icon.text_color = (0.1, 0.8, 0.6, 1)
        self.overlay_status.text = "Tap NFC Tag Now"
        
        # Clear fields
        self._set_format(self.selected_format)
        
        if hasattr(self, "debug_btn"):
            self.debug_btn.disabled = True

    def _open_mock_dialog(self, button):
        # Allow triggering mock card tap on desktop inside writing mode
        dialog = MockNFCScanDialog(self.bridge)
        dialog.show()
