from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from database.repository import get_all_tags, delete_tag
from ui.components.cards import VaultTagCard
from kivymd.uix.snackbar import Snackbar

class VaultScreen(MDScreen):
    def __init__(self, bridge, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge
        self.name = "vault"
        
        self._build_ui()
        # Bind screen transition to refresh stored cards
        self.bind(on_pre_enter=self.on_refresh)

    def _build_ui(self):
        self.main_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(16)
        )

        # Header Title
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        header.add_widget(MDLabel(
            text="Secure Encrypted Vault",
            font_style="H5",
            bold=True
        ))
        
        # Refresh Button
        refresh_btn = MDIconButton(
            icon="refresh",
            pos_hint={"center_y": 0.5},
            on_release=self.on_refresh
        )
        header.add_widget(refresh_btn)
        self.main_layout.add_widget(header)

        # Scrollview containing cards
        self.scroll_view = ScrollView()
        
        # Scroll container
        self.list_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None
        )
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        
        self.scroll_view.add_widget(self.list_container)
        self.main_layout.add_widget(self.scroll_view)

        # Empty vault notification label
        self.empty_lbl = MDLabel(
            text="Your vault is currently empty.\nScan physical cards to save them securely.",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(100),
            pos_hint={"center_y": 0.5}
        )

        self.add_widget(self.main_layout)

    def on_refresh(self, *args):
        """Fetches decrypted database items and rebuilds the visual list."""
        self.list_container.clear_widgets()
        
        tags = get_all_tags()
        if not tags:
            if self.empty_lbl not in self.main_layout.children:
                # Insert empty notice instead of scrollview
                self.main_layout.remove_widget(self.scroll_view)
                self.main_layout.add_widget(self.empty_lbl)
        else:
            if self.empty_lbl in self.main_layout.children:
                self.main_layout.remove_widget(self.empty_lbl)
            if self.scroll_view not in self.main_layout.children:
                self.main_layout.add_widget(self.scroll_view)

            # Build cards
            for tag in tags:
                card = VaultTagCard(
                    tag=tag,
                    on_delete=self._delete_card,
                    on_emulate=self._emulate_card
                )
                self.list_container.add_widget(card)

    def _delete_card(self, tag):
        uid = tag.get("uid")
        name = tag.get("name", "Unnamed Tag")
        
        success = delete_tag(uid)
        if success:
            Snackbar(
                text=f"Removed '{name}' from Vault.",
                bg_color=(0.8, 0.2, 0.2, 1),
                duration=2.0
            ).open()
            self.on_refresh()

    def _emulate_card(self, tag):
        name = tag.get("name", "Unnamed Tag")
        
        # Turn on emulation
        self.bridge.set_hce_state(True)
        
        Snackbar(
            text=f"Emulating secure digital badge for '{name}'...",
            bg_color=(0.1, 0.6, 0.4, 1),
            duration=3.0
        ).open()
