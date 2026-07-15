from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDIconButton
from kivy.metrics import dp
from kivy.clock import Clock
from database.repository import get_all_tags

class DashboardScreen(MDScreen):
    def __init__(self, bridge, switch_to_screen_fn, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge
        self.switch_to_screen = switch_to_screen_fn
        self.name = "dashboard"
        
        self._build_ui()
        # Periodically refresh counters when the screen is viewed
        self.bind(on_pre_enter=self.on_refresh)

    def _build_ui(self):
        # Outer wrapper
        main_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(20)
        )

        # Header Title
        title_box = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        title_box.add_widget(MDLabel(
            text="NFC Vault & Badge",
            font_style="H5",
            bold=True,
            theme_text_color="Primary"
        ))
        
        # Add light/dark switcher button
        self.theme_btn = MDIconButton(
            icon="weather-night",
            pos_hint={"center_y": 0.5},
            on_release=self._toggle_theme
        )
        title_box.add_widget(self.theme_btn)
        main_layout.add_widget(title_box)

        # System Status Card
        self.status_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(4),
            size_hint_y=None,
            height=dp(80),
            radius=[dp(16)],
            elevation=1
        )
        self.status_title = MDLabel(
            text="System Diagnostics",
            font_style="Subtitle2",
            theme_text_color="Hint"
        )
        self.status_label = MDLabel(
            text="Scanner ready",
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Secondary"
        )
        self.status_card.add_widget(self.status_title)
        self.status_card.add_widget(self.status_label)
        main_layout.add_widget(self.status_card)

        # Big Scan Activation Button (Floating Center Widget)
        center_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        
        # Giant Scan Icon Button
        self.scan_pulse_btn = MDIconButton(
            icon="nfc-variant",
            user_font_size="96sp",
            theme_text_color="Custom",
            text_color=(0.55, 0.35, 0.85, 1),
            pos_hint={"center_x": 0.5},
            on_release=self._trigger_scanner_nav
        )
        
        scan_label = MDLabel(
            text="Tap here to Scan NFC Tag",
            font_style="H6",
            bold=True,
            halign="center",
            theme_text_color="Primary"
        )
        
        center_box.add_widget(self.scan_pulse_btn)
        center_box.add_widget(scan_label)
        main_layout.add_widget(center_box)

        # Stats Cards Layout (Emulation State and Vault Item Counter)
        stats_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(16),
            size_hint_y=None,
            height=dp(130)
        )

        # Emulation Badge card
        self.emul_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            radius=[dp(16)],
            elevation=1
        )
        self.emul_card.add_widget(MDIconButton(icon="remote", user_font_size="24sp", theme_text_color="Custom", text_color=(0.1, 0.8, 0.6, 1)))
        self.emul_card.add_widget(MDLabel(text="Badge Emulation", font_style="Caption", theme_text_color="Hint"))
        self.emul_lbl = MDLabel(text="Disabled", font_style="Subtitle1", bold=True)
        self.emul_card.add_widget(self.emul_lbl)
        
        # Vault Counter card
        self.vault_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            radius=[dp(16)],
            elevation=1,
            on_release=self._navigate_to_vault
        )
        self.vault_card.add_widget(MDIconButton(icon="safe", user_font_size="24sp", theme_text_color="Custom", text_color=(0.9, 0.6, 0.1, 1)))
        self.vault_card.add_widget(MDLabel(text="Encrypted Vault", font_style="Caption", theme_text_color="Hint"))
        self.vault_lbl = MDLabel(text="0 Cards Saved", font_style="Subtitle1", bold=True)
        self.vault_card.add_widget(self.vault_lbl)

        stats_layout.add_widget(self.emul_card)
        stats_layout.add_widget(self.vault_card)
        main_layout.add_widget(stats_layout)

        self.add_widget(main_layout)

    def on_refresh(self, *args):
        # Update tags count in database
        try:
            tags = get_all_tags()
            count = len(tags)
            self.vault_lbl.text = f"{count} Tag{'s' if count != 1 else ''} Saved"
        except Exception:
            self.vault_lbl.text = "0 Tags Saved"
            
        # Update HCE Emulation state text
        if hasattr(self.bridge.impl, "hce_enabled") and self.bridge.impl.hce_enabled:
            self.emul_lbl.text = "Active\n(AID F0010203040506)"
            self.emul_lbl.theme_text_color = "Custom"
            self.emul_lbl.text_color = (0.1, 0.8, 0.6, 1)
        else:
            self.emul_lbl.text = "Disabled"
            self.emul_lbl.theme_text_color = "Primary"

    def update_system_status(self, status: str):
        self.status_label.text = status

    def _trigger_scanner_nav(self, button):
        # Trigger the global iOS-style bottom sheet scan modal
        app_layout = self.switch_to_screen.__self__
        
        def _on_tag_processed(tag_info):
            # Navigate to the scanner screen
            self.switch_to_screen("scanner")
            # Populate scanner screen results
            if hasattr(app_layout, "scanner_screen"):
                app_layout.scanner_screen.on_tag_scanned(tag_info)
                
        app_layout.show_nfc_sheet(mode="read", on_tag_processed=_on_tag_processed)

    def _navigate_to_vault(self, card):
        self.switch_to_screen("vault")

    def _toggle_theme(self, button):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            app.theme_cls.theme_style = "Light"
            self.theme_btn.icon = "weather-sunny"
        else:
            app.theme_cls.theme_style = "Dark"
            self.theme_btn.icon = "weather-night"
        # Refresh current UI statuses
        self.on_refresh()
