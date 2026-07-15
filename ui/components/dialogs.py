from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu

# Simulation presets
PRESETS = [
    {
        "name": "Elevator Pass (13.56MHz)",
        "uid": "AB:89:C3:DF:11",
        "type": "Mifare Classic 1K",
        "payload": "SECURE_SECTOR_0_KEY: [9A F3 D1 AA BE D2]"
    },
    {
        "name": "Gym Access Card",
        "uid": "12:34:56:78:90",
        "type": "Generic HF Card",
        "payload": "GYM_MEMBER_ID: #40293-EN2"
    },
    {
        "name": "Wi-Fi NDEF Record",
        "uid": "44:CC:33:EE:00",
        "type": "NDEF Tag",
        "payload": "WIFI:S:GuestNet;T:WPA;P:guest1234;;"
    },
    {
        "name": "Personal Website URL",
        "uid": "77:88:99:AA:BB",
        "type": "NDEF Tag",
        "payload": "URL: https://github.com/google/gemini"
    },
    {
        "name": "Blank Tag (NDEF Format)",
        "uid": "00:11:22:33:44",
        "type": "NDEF Tag",
        "payload": ""
    }
]

class MockNFCScanDialog:
    def __init__(self, bridge, on_complete=None):
        self.bridge = bridge
        self.on_complete = on_complete
        self.dialog = None
        self.preset_menu = None
        self._build_dialog()

    def _build_dialog(self):
        # Textfields for details
        self.txt_name = MDTextField(
            text=PRESETS[0]["name"],
            hint_text="Preset / Label",
            helper_text="Choose preset or enter custom",
            helper_text_mode="on_focus"
        )
        self.txt_uid = MDTextField(
            text=PRESETS[0]["uid"],
            hint_text="NFC Tag UID",
            helper_text="Format: XX:XX:XX:XX",
            helper_text_mode="on_focus"
        )
        self.txt_type = MDTextField(
            text=PRESETS[0]["type"],
            hint_text="Hardware Chip Type",
            helper_text="e.g. Mifare, NDEF, ISO-DEP",
            helper_text_mode="on_focus"
        )
        self.txt_payload = MDTextField(
            text=PRESETS[0]["payload"],
            hint_text="NDEF Payload / Raw Data",
            multiline=True,
            max_height="80dp"
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            height="340dp"
        )
        
        # Add button to select presets
        preset_btn = MDRaisedButton(
            text="Choose Simulation Preset",
            pos_hint={"center_x": 0.5},
            on_release=self._open_presets
        )
        
        content.add_widget(preset_btn)
        content.add_widget(self.txt_name)
        content.add_widget(self.txt_uid)
        content.add_widget(self.txt_type)
        content.add_widget(self.txt_payload)

        # Dialog buttons
        self.dialog = MDDialog(
            title="Desktop Tag Simulator",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=self.dismiss
                ),
                MDRaisedButton(
                    text="TAP CARD TO DEVICE",
                    on_release=self._simulate_scan
                ),
            ],
        )
        
        # Dropdown menu items
        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": preset["name"],
                "on_release": lambda x=preset: self._apply_preset(x),
            }
            for preset in PRESETS
        ]
        self.preset_menu = MDDropdownMenu(
            caller=preset_btn,
            items=menu_items,
            width_mult=4,
        )

    def _open_presets(self, button):
        self.preset_menu.open()

    def _apply_preset(self, preset):
        self.preset_menu.dismiss()
        self.txt_name.text = preset["name"]
        self.txt_uid.text = preset["uid"]
        self.txt_type.text = preset["type"]
        self.txt_payload.text = preset["payload"]

    def _simulate_scan(self, button):
        uid = self.txt_uid.text.strip()
        tag_type = self.txt_type.text.strip()
        payload = self.txt_payload.text.strip()
        
        if not uid or not tag_type:
            return
            
        # Trigger simulation logic in the mock implementation
        if hasattr(self.bridge.impl, "trigger_mock_tag"):
            self.bridge.impl.trigger_mock_tag(uid, tag_type, payload)
            
        self.dismiss()
        if self.on_complete:
            self.on_complete()

    def show(self):
        self.dialog.open()

    def dismiss(self, *args):
        if self.dialog:
            self.dialog.dismiss()


class SaveTagDialog:
    def __init__(self, tag_info, on_save):
        self.tag_info = tag_info
        self.on_save = on_save
        self.dialog = None
        self._build_dialog()

    def _build_dialog(self):
        content = MDBoxLayout(
            orientation="vertical",
            spacing="12dp",
            size_hint_y=None,
            height="100dp"
        )
        
        # Prepopulate name based on type
        default_name = f"My {self.tag_info['type']}"
        self.txt_name = MDTextField(
            text=default_name,
            hint_text="Save Label / Name",
            helper_text="e.g. Lobby Gate, Elevator Tag",
            helper_text_mode="on_focus"
        )
        content.add_widget(self.txt_name)

        self.dialog = MDDialog(
            title="Save Scan to Secure Vault?",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="DISCARD",
                    on_release=self.dismiss
                ),
                MDRaisedButton(
                    text="SAVE ENCRYPTED",
                    on_release=self._save
                ),
            ],
        )

    def _save(self, button):
        name = self.txt_name.text.strip()
        if not name:
            name = f"My {self.tag_info['type']}"
            
        # Invoke callback
        self.on_save(name)
        self.dismiss()

    def show(self):
        self.dialog.open()

    def dismiss(self, *args):
        if self.dialog:
            self.dialog.dismiss()
