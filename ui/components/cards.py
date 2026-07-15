from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.fitimage import FitImage
from kivy.metrics import dp
from config import THEME_PRIMARY

class NFCInfoCard(MDCard):
    """A premium card widget to present diagnostic read metrics of scanned NFC tags."""
    def __init__(self, tag_info, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(200)
        self.padding = dp(16)
        self.spacing = dp(8)
        self.radius = [dp(16)]
        self.elevation = 2
        
        # Color matching
        self.line_color = (0.2, 0.2, 0.2, 0.5)
        self.line_width = dp(1)

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
        payload = tag.get("payload", "").lower()
        if "wifi:" in payload:
            icon = "wifi"
        elif "url:" in payload or "http" in payload:
            icon = "link"
        elif "sector" in payload or "key" in payload or "pass" in payload:
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
        
        # Emulate button (Only if emulation tags)
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
