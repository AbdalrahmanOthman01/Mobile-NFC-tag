import os
import sys
import unittest
from pathlib import Path

# Add root folder to path so imports work correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set environment variable to use mock/test DB before imports
os.environ["KIVY_NO_CONSOLELOG"] = "1"  # Silence Kivy logs during tests
os.environ["KIVY_NO_ARGS"] = "1"        # Disable Kivy intercepting sys.argv

from config import DB_PATH
from database.connection import initialize_db, get_connection
from database.repository import save_tag, get_tag_by_uid, get_all_tags, delete_tag, log_written_record, get_written_logs

class TestEncryptedDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Guarantee db is initialized
        initialize_db()

    def test_01_save_and_decrypt_tag(self):
        uid = "AA:BB:CC:DD"
        tag_type = "Mifare Classic Test"
        name = "Office Door"
        payload = "SECRET_PASSCODE_12345"

        # Save tag (encryptions happen internally)
        success = save_tag(uid, tag_type, name, payload, is_emulatable=True)
        self.assertTrue(success)

        # Retrieve tag
        tag = get_tag_by_uid(uid)
        self.assertIsNotNone(tag)
        self.assertEqual(tag["uid"], uid)
        self.assertEqual(tag["tag_type"], tag_type)
        self.assertEqual(tag["name"], name)
        
        # Verify automatic decryption
        self.assertEqual(tag["payload"], payload)
        self.assertTrue(tag["is_emulatable"])

    def test_02_all_tags_and_deletion(self):
        # Insert a secondary tag
        save_tag("11:22:33:44", "NDEF URL", "Git Link", "https://github.com")

        # Get all tags
        all_tags = get_all_tags()
        self.assertGreaterEqual(len(all_tags), 2)

        # Test deletion
        success = delete_tag("AA:BB:CC:DD")
        self.assertTrue(success)

        # Confirm deleted
        tag = get_tag_by_uid("AA:BB:CC:DD")
        self.assertIsNone(tag)

    def test_03_write_logs(self):
        payload_type = "WIFI"
        payload = "WIFI:S:OfficeWifi;T:WPA;P:secretPass;;"

        success = log_written_record(payload_type, payload)
        self.assertTrue(success)

        logs = get_written_logs()
        self.assertGreater(len(logs), 0)
        self.assertEqual(logs[0]["payload_type"], payload_type)
        self.assertEqual(logs[0]["payload"], payload)

if __name__ == "__main__":
    unittest.main()
