import logging
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.graphics import Color, Line

logger = logging.getLogger(__name__)

class PulseRing(Widget):
    """Concentric animated ring drawn using canvas line instructions."""
    radius = NumericProperty(dp(40))
    opacity_val = NumericProperty(0.6)
    color = ListProperty([0.55, 0.35, 0.85])  # Primary Theme Purple

    def __init__(self, start_pos, **kwargs):
        super().__init__(**kwargs)
        self.center = start_pos
        with self.canvas:
            self.canvas_color = Color(rgba=(self.color[0], self.color[1], self.color[2], self.opacity_val))
            self.canvas_line = Line(circle=(self.center_x, self.center_y, self.radius), width=dp(2))
        self.bind(pos=self._update_canvas, size=self._update_canvas, radius=self._update_canvas, opacity_val=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas_color.rgba = (self.color[0], self.color[1], self.color[2], self.opacity_val)
        self.canvas_line.circle = (self.center_x, self.center_y, self.radius)

    def start_animation(self):
        anim = Animation(radius=dp(130), opacity_val=0, duration=1.6, transition="out_quad")
        anim.bind(on_complete=lambda *x: self.parent.remove_widget(self) if self.parent else None)
        anim.start(self)


class IOSNFCSheet(MDFloatLayout):
    """A premium iOS-style bottom sheet modal to handle NFC interactions with smooth animations."""
    
    title_text = StringProperty("Ready to Scan")
    helper_text = StringProperty("Hold your device near the NFC tag.")
    
    def __init__(self, bridge, app_layout, **kwargs):
        super().__init__(**kwargs)
        self.bridge = bridge
        self.app_layout = app_layout
        
        # State variables
        self.mode = "read"  # "read" or "write"
        self.payload_type = None
        self.payload_data = None
        self.on_tag_processed = None  # Callback signature: fn(tag_info: dict)
        self.state = "hidden"  # "hidden", "scanning", "success", "failed"
        self._pulse_event = None
        
        # UI Properties
        self.size_hint = (1, 1)
        self.opacity = 0
        self.disabled = True
        
        self._build_ui()

    def _build_ui(self):
        # 1. Semi-transparent backdrop overlay
        self.backdrop = Widget(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0}
        )
        # Draw dark backdrop on canvas
        with self.backdrop.canvas:
            self.backdrop_color = Color(0, 0, 0, 0)
            from kivy.graphics import Rectangle
            self.backdrop_rect = Rectangle(size=self.backdrop.size, pos=self.backdrop.pos)
        
        self.backdrop.bind(pos=self._update_backdrop, size=self._update_backdrop)
        self.add_widget(self.backdrop)
        
        # 2. Sliding Card Container
        self.sheet_card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(340),
            pos_hint={"x": 0, "y": -1},  # Start completely hidden off-screen
            radius=[dp(24), dp(24), 0, 0],
            elevation=4,
            padding=dp(20),
            spacing=dp(16)
        )
        
        # Title Label
        self.title_lbl = MDLabel(
            text=self.title_text,
            font_style="H6",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        self.sheet_card.add_widget(self.title_lbl)
        
        # Animation Graphics Container (holds pulsing circles and central icon)
        self.graphics_container = FloatLayout(
            size_hint=(1, 1)
        )
        
        # Center Icon
        self.center_icon = MDIconButton(
            icon="nfc-variant",
            user_font_size="72sp",
            theme_text_color="Custom",
            text_color=(0.55, 0.35, 0.85, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        self.graphics_container.add_widget(self.center_icon)
        self.sheet_card.add_widget(self.graphics_container)
        
        # Instructions/Helper Label
        self.helper_lbl = MDLabel(
            text=self.helper_text,
            font_style="Subtitle2",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(40)
        )
        self.sheet_card.add_widget(self.helper_lbl)
        
        # Action Buttons Layout (Side-by-side on desktop for easy debugging)
        from kivymd.uix.boxlayout import MDBoxLayout
        btn_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10)
        )
        
        self.action_btn = MDFlatButton(
            text="CANCEL",
            theme_text_color="Custom",
            text_color=(0.9, 0.3, 0.3, 1),
            size_hint_x=0.5,
            on_release=self._on_action_button_pressed
        )
        btn_layout.add_widget(self.action_btn)
        
        from kivy.utils import platform
        if platform not in ("android", "ios"):
            self.debug_sim_btn = MDFlatButton(
                text="SIMULATE TAP",
                theme_text_color="Custom",
                text_color=(0.9, 0.4, 0.1, 1),
                size_hint_x=0.5,
                on_release=self._open_desktop_simulator
            )
            btn_layout.add_widget(self.debug_sim_btn)
            
        self.sheet_card.add_widget(btn_layout)
        
        self.add_widget(self.sheet_card)

    def _open_desktop_simulator(self, button):
        from ui.components.dialogs import MockNFCScanDialog
        dialog = MockNFCScanDialog(self.bridge)
        dialog.show()

    def _update_backdrop(self, *args):
        self.backdrop_rect.pos = self.backdrop.pos
        self.backdrop_rect.size = self.backdrop.size

    def show(self, mode="read", payload_type=None, payload_data=None, on_tag_processed=None):
        """Slides up the bottom sheet and initiates the NFC loop."""
        if self.state != "hidden":
            return
            
        self.mode = mode
        self.payload_type = payload_type
        self.payload_data = payload_data
        self.on_tag_processed = on_tag_processed
        
        # Configure initial UI states
        self.opacity = 1
        self.disabled = False
        self.state = "scanning"
        self.action_btn.text = "CANCEL"
        self.action_btn.text_color = (0.9, 0.3, 0.3, 1)
        
        if self.mode == "read":
            self.title_lbl.text = "Ready to Scan"
            self.helper_lbl.text = "Hold your device near the NFC tag."
        else:
            self.title_lbl.text = f"Ready to Write {self.payload_type}"
            self.helper_lbl.text = "Ready to format tag. Touch NFC tag now."
            
        self.center_icon.icon = "nfc-variant"
        self.center_icon.text_color = (0.55, 0.35, 0.85, 1)
        self.center_icon.user_font_size = "72sp"
        
        # Slide sheet card up and fade backdrop color in
        Animation(y=0, duration=0.35, transition="out_quad").start(self.sheet_card)
        Animation(rgba=(0, 0, 0, 0.4), duration=0.35).start(self.backdrop_color)
        
        # Hook up hardware callbacks
        self.bridge.on_tag_scanned = self._on_tag_scanned
        self.bridge.on_tag_written = self._on_tag_written
        self.bridge.on_status_changed = self._on_status_changed
        
        # Start scanning or arm writing
        if self.mode == "read":
            self.bridge.start_scan()
        else:
            self.bridge.prepare_write(self.payload_type, self.payload_data)
            
        # Start pulsing animation loop
        self._start_pulsing()

    def dismiss(self, *args):
        """Slides down the sheet card and resets state."""
        if self.state == "hidden":
            return
            
        self._stop_pulsing()
        
        # Stop scan or write state in bridge
        if self.mode == "read":
            self.bridge.stop_scan()
        else:
            self.bridge.cancel_write()
            
        self.state = "hidden"
        self.disabled = True
        
        # Slide sheet down and fade backdrop out
        anim_card = Animation(y=-self.sheet_card.height, duration=0.3, transition="in_quad")
        anim_backdrop = Animation(rgba=(0, 0, 0, 0), duration=0.3)
        
        def _on_finish(*x):
            self.opacity = 0
            
        anim_card.bind(on_complete=_on_finish)
        anim_card.start(self.sheet_card)
        anim_backdrop.start(self.backdrop_color)

    def _start_pulsing(self):
        self._stop_pulsing()
        self._spawn_ring()
        self._pulse_event = Clock.schedule_interval(self._spawn_ring, 0.8)

    def _stop_pulsing(self):
        if self._pulse_event:
            self._pulse_event.cancel()
            self._pulse_event = None
            
        # Remove any existing rings
        rings = [c for c in self.graphics_container.children if isinstance(c, PulseRing)]
        for r in rings:
            self.graphics_container.remove_widget(r)

    def _spawn_ring(self, *args):
        # Calculate local center coordinates of graphics container
        cx = self.graphics_container.center_x - self.graphics_container.x
        cy = self.graphics_container.center_y - self.graphics_container.y
        
        ring = PulseRing(
            start_pos=(cx, cy),
            color=[0.55, 0.35, 0.85] if self.mode == "read" else [0.1, 0.8, 0.6]
        )
        self.graphics_container.add_widget(ring)
        # Draw on top of backdrop but behind icon
        self.graphics_container.remove_widget(self.center_icon)
        self.graphics_container.add_widget(self.center_icon)
        ring.start_animation()

    def _on_action_button_pressed(self, button):
        if self.state in ("success", "failed"):
            self.dismiss()
        else:
            self.dismiss()

    def _on_status_changed(self, status: str):
        if self.state == "scanning":
            self.helper_lbl.text = status

    def _on_tag_scanned(self, tag_info: dict):
        """Callback from physical bridge when a card is touched."""
        if self.state != "scanning":
            return
            
        self._stop_pulsing()
        self.state = "success"
        
        # Visual transition
        self.title_lbl.text = "Scan Complete"
        self.helper_lbl.text = f"Successfully read tag ID: {tag_info.get('uid')}"
        
        # Success Icon & Bounce Animation
        self.center_icon.icon = "check-circle"
        self.center_icon.text_color = (0.1, 0.8, 0.4, 1)
        self.center_icon.user_font_size = "10sp"
        anim = Animation(user_font_size="84sp", duration=0.2, transition="out_bounce") + \
               Animation(user_font_size="72sp", duration=0.1)
        anim.start(self.center_icon)
        
        self.action_btn.text = "DONE"
        self.action_btn.text_color = (0.1, 0.8, 0.4, 1)
        
        # Dispatch tag information back to caller
        if self.on_tag_processed:
            self.on_tag_processed(tag_info)
            
        # Automatically slide down after 1.8 seconds
        Clock.schedule_once(self.dismiss, 1.8)

    def _on_tag_written(self, success: bool, message: str):
        """Callback from bridge for writing transactions."""
        if self.state != "scanning":
            return
            
        self._stop_pulsing()
        
        if success:
            self.state = "success"
            self.title_lbl.text = "Write Complete"
            self.helper_lbl.text = message
            
            self.center_icon.icon = "check-circle"
            self.center_icon.text_color = (0.1, 0.8, 0.4, 1)
            self.center_icon.user_font_size = "10sp"
            anim = Animation(user_font_size="84sp", duration=0.2, transition="out_bounce") + \
                   Animation(user_font_size="72sp", duration=0.1)
            anim.start(self.center_icon)
            
            self.action_btn.text = "DONE"
            self.action_btn.text_color = (0.1, 0.8, 0.4, 1)
            
            if self.on_tag_processed:
                self.on_tag_processed({"success": True, "message": message})
                
            Clock.schedule_once(self.dismiss, 1.8)
        else:
            self.state = "failed"
            self.title_lbl.text = "Write Failed"
            self.helper_lbl.text = message
            
            self.center_icon.icon = "close-circle"
            self.center_icon.text_color = (0.9, 0.3, 0.3, 1)
            self.center_icon.user_font_size = "10sp"
            anim = Animation(user_font_size="84sp", duration=0.2, transition="out_bounce") + \
                   Animation(user_font_size="72sp", duration=0.1)
            anim.start(self.center_icon)
            
            self.action_btn.text = "TRY AGAIN"
            self.action_btn.text_color = (0.9, 0.4, 0.1, 1)

    def on_touch_down(self, touch):
        # Prevent clicks from filtering through to background screens if visible
        if self.state != "hidden":
            super().on_touch_down(touch)
            
            # If clicked on background backdrop, dismiss sheet (unless actively scanning)
            if not self.sheet_card.collide_point(*touch.pos):
                if self.state in ("success", "failed"):
                    self.dismiss()
            return True
        return False
