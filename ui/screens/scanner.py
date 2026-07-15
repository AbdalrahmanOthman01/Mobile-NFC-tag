from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.progressbar import MDProgressBar
from kivy.metrics import dp
from kivy.utils import platform
from ui.components.cards import NFCInfoCard
from ui.components.dialogs import MockNFCScanDialog, SaveTagDialog
from database.repository import save_tag

class ScannerScreen(MDScreen):
    def __init__(self, bridge, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge
        self.name = "scanner"
        
        # Scanned state
        self.scanned_tag = None
        
        self._build_ui()
        
        # Bind screen enter/exit transitions to start/stop physical reading
        self.bind(on_enter=self.on_screen_enter)
        self.bind(on_leave=self.on_screen_leave)

    def _build_ui(self):
        self.main_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(20)
        )

        # Header title
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        header.add_widget(MDLabel(
            text="NFC Diagnostic Scanner",
            font_style="H5",
            bold=True
        ))
        self.main_layout.add_widget(header)

        # Dynamic Status Container
        self.status_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        
        self.pulse_icon = MDIconButton(
            icon="nfc-search-variant",
            user_font_size="80sp",
            theme_text_color="Custom",
            text_color=(0.55, 0.35, 0.85, 1),
            pos_hint={"center_x": 0.5},
            on_release=self._trigger_nfc_sheet
        )
        self.status_box.add_widget(self.pulse_icon)

        self.status_lbl = MDLabel(
            text="Tap icon to start scanning. Hold tag near the back of the device.",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Secondary"
        )
        self.status_box.add_widget(self.status_lbl)
        
        # Progress Bar (Pulsing scan activity placeholder)
        self.progress_bar = MDProgressBar(
            value=0,
            size_hint_x=0.8,
            pos_hint={"center_x": 0.5}
        )
        self.status_box.add_widget(self.progress_bar)
        
        self.main_layout.add_widget(self.status_box)

        # Dynamic Result Container (Holds NFCInfoCard when scanned)
        self.result_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            size_hint_y=None,
            height=dp(280),
            opacity=0  # Invisible initially
        )
        self.main_layout.add_widget(self.result_box)

        # Action Buttons Layout
        self.actions_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(16),
            size_hint_y=None,
            height=dp(50),
            opacity=0  # Invisible initially
        )
        
        self.btn_save = MDRaisedButton(
            text="SAVE ENCRYPTED",
            size_hint_x=0.5,
            on_release=self._open_save_dialog
        )
        self.btn_retry = MDFillRoundFlatButton(
            text="SCAN AGAIN",
            size_hint_x=0.5,
            on_release=self._reset_scanner
        )
        
        self.actions_layout.add_widget(self.btn_save)
        self.actions_layout.add_widget(self.btn_retry)
        self.main_layout.add_widget(self.actions_layout)

        # Desktop Debug Option: Trigger Dialog
        if platform not in ("android", "ios"):
            debug_box = MDBoxLayout(size_hint_y=None, height=dp(50), padding=[0, dp(10)])
            debug_btn = MDRaisedButton(
                text="DEBUG: Trigger Tag Simulator",
                md_bg_color=(0.9, 0.4, 0.1, 1),
                pos_hint={"center_x": 0.5},
                on_release=self._open_mock_dialog
            )
            debug_box.add_widget(debug_btn)
            self.main_layout.add_widget(debug_box)

        self.add_widget(self.main_layout)

    def _trigger_nfc_sheet(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if hasattr(app, "root") and app.root:
            app.root.show_nfc_sheet(mode="read", on_tag_processed=self.on_tag_scanned)

    def on_screen_enter(self, *args):
        if not self.scanned_tag:
            self._trigger_nfc_sheet()

    def on_screen_leave(self, *args):
        # Dismiss global NFC sheet if open and active
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if hasattr(app.root, "nfc_sheet") and app.root.nfc_sheet.state != "hidden":
            app.root.nfc_sheet.dismiss()

    def on_status_changed(self, status: str):
        if not self.scanned_tag:
            self.status_lbl.text = status

    def on_tag_scanned(self, tag_info: dict):
        """Called when a card is scanned."""
        self.scanned_tag = tag_info
        
        # Display the result view
        self.result_box.clear_widgets()
        self.result_box.add_widget(NFCInfoCard(tag_info))
        
        # Toggle Layout Transparencies
        self.status_box.opacity = 0
        self.status_box.size_hint_y = None
        self.status_box.height = 0
        
        self.result_box.opacity = 1
        self.actions_layout.opacity = 1

    def _open_save_dialog(self, button):
        if not self.scanned_tag:
            return
        dialog = SaveTagDialog(self.scanned_tag, self._save_tag)
        dialog.show()

    def _save_tag(self, custom_name: str):
        success = save_tag(
            uid=self.scanned_tag["uid"],
            tag_type=self.scanned_tag["type"],
            name=custom_name,
            payload=self.scanned_tag["payload"],
            is_emulatable=True
        )
        if success:
            self._reset_scanner()

    def _reset_scanner(self, *args):
        self.scanned_tag = None
        
        # Restore scan layout
        self.result_box.opacity = 0
        self.actions_layout.opacity = 0
        
        self.status_box.size_hint_y = 1
        self.status_box.opacity = 1
        self.status_lbl.text = "Tap icon to start scanning."
        
        # Re-trigger bottom sheet scan
        self._trigger_nfc_sheet()

    def _open_mock_dialog(self, button):
        # Utility to trigger simulation popup on desktop
        dialog = MockNFCScanDialog(self.bridge)
        dialog.show()
