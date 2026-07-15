from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from ui.screens.dashboard import DashboardScreen
from ui.screens.scanner import ScannerScreen
from ui.screens.writer import WriterScreen
from ui.screens.vault import VaultScreen

class AppLayout(MDBoxLayout):
    """The root layout containing bottom tabs navigation and page handlers."""
    def __init__(self, bridge, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.bridge = bridge

        # Bottom navigation
        self.nav = MDBottomNavigation()

        # 1. Dashboard Tab
        self.tab_dashboard = MDBottomNavigationItem(
            name="dashboard_tab",
            text="Home",
            icon="home-outline"
        )
        self.dashboard_screen = DashboardScreen(
            bridge=self.bridge,
            switch_to_screen_fn=self.switch_to_screen
        )
        self.tab_dashboard.add_widget(self.dashboard_screen)

        # 2. Scanner Tab
        self.tab_scanner = MDBottomNavigationItem(
            name="scanner_tab",
            text="Scan",
            icon="nfc"
        )
        self.scanner_screen = ScannerScreen(bridge=self.bridge)
        self.tab_scanner.add_widget(self.scanner_screen)

        # 3. Writer Tab
        self.tab_writer = MDBottomNavigationItem(
            name="writer_tab",
            text="Write",
            icon="database-edit"
        )
        self.writer_screen = WriterScreen(bridge=self.bridge)
        self.tab_writer.add_widget(self.writer_screen)

        # 4. Vault Tab
        self.tab_vault = MDBottomNavigationItem(
            name="vault_tab",
            text="Vault",
            icon="safe"
        )
        self.vault_screen = VaultScreen(bridge=self.bridge)
        self.tab_vault.add_widget(self.vault_screen)

        # Add items to nav
        self.nav.add_widget(self.tab_dashboard)
        self.nav.add_widget(self.tab_scanner)
        self.nav.add_widget(self.tab_writer)
        self.nav.add_widget(self.tab_vault)
        
        self.add_widget(self.nav)

        # Hook status updates from bridge to dashboard diagnostic label
        self.bridge.on_status_changed = self.on_nfc_status_changed

    def switch_to_screen(self, screen_name: str):
        """Helper to navigate programmatically between tabs."""
        if screen_name == "scanner":
            self.nav.switch_tab("scanner_tab")
        elif screen_name == "vault":
            self.nav.switch_tab("vault_tab")
        elif screen_name == "dashboard":
            self.nav.switch_tab("dashboard_tab")

    def on_nfc_status_changed(self, status: str):
        # Delegate status updates to dashboard layout card label
        if hasattr(self.dashboard_screen, "update_system_status"):
            self.dashboard_screen.update_system_status(status)
            
        # Also pass it down to current active views if they listen
        current_tab = self.nav.current_tab_name
        if current_tab == "scanner_tab" and hasattr(self.scanner_screen, "on_status_changed"):
            self.scanner_screen.on_status_changed(status)
        elif current_tab == "writer_tab" and hasattr(self.writer_screen, "on_status_changed"):
            self.writer_screen.on_status_changed(status)
