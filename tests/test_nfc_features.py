import sys
import os
import unittest
from pathlib import Path

# Add root folder to path so imports work correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nfc.parsers import make_vcard, parse_vcard, make_file_payload, parse_file_payload
from database.connection import initialize_db
from database.repository import save_tag, get_tag_by_uid, delete_tag

class TestNFCFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_db()

    def test_vcard_creation_and_parsing(self):
        first_name = "Jane"
        last_name = "Doe"
        phone = "+1-555-0199"
        email = "jane.doe@example.com"
        company = "Acme Corp"
        website = "https://example.com"

        vcard_str = make_vcard(first_name, last_name, phone, email, company, website)
        self.assertIn("BEGIN:VCARD", vcard_str)
        self.assertIn("VERSION:3.0", vcard_str)
        self.assertIn("N:Doe;Jane;;;", vcard_str)
        self.assertIn("FN:Jane Doe", vcard_str)
        self.assertIn("TEL;TYPE=CELL:+1-555-0199", vcard_str)
        self.assertIn("EMAIL;TYPE=PREF,INTERNET:jane.doe@example.com", vcard_str)
        self.assertIn("ORG:Acme Corp", vcard_str)
        self.assertIn("URL:https://example.com", vcard_str)
        self.assertIn("END:VCARD", vcard_str)

        # Test parser
        parsed = parse_vcard(vcard_str)
        self.assertEqual(parsed["first_name"], first_name)
        self.assertEqual(parsed["last_name"], last_name)
        self.assertEqual(parsed["phone"], phone)
        self.assertEqual(parsed["email"], email)
        self.assertEqual(parsed["company"], company)
        self.assertEqual(parsed["website"], website)

    def test_file_serialization_and_parsing(self):
        filename = "config.json"
        mime_type = "application/json"
        content = '{"theme": "dark", "version": 2}'

        payload_str = make_file_payload(filename, mime_type, content)
        self.assertIn(filename, payload_str)
        self.assertIn(mime_type, payload_str)

        # Test parser
        parsed = parse_file_payload(payload_str)
        self.assertEqual(parsed["name"], filename)
        self.assertEqual(parsed["mime"], mime_type)
        self.assertEqual(parsed["content"], content)
        self.assertEqual(parsed["raw_bytes"], content.encode("utf-8"))

    def test_database_persistence(self):
        # Save a vCard tag
        uid = "VC:11:22:33:44"
        vcard_payload = "VCARD:" + make_vcard("John", "Smith", "911", "john@smith.com", "Test Inc", "")
        success = save_tag(uid, "NDEF Tag", "John Smith Contact", vcard_payload, is_emulatable=False)
        self.assertTrue(success)

        # Retrieve and verify
        tag = get_tag_by_uid(uid)
        self.assertIsNotNone(tag)
        self.assertEqual(tag["payload"], vcard_payload)

        # Delete to clean up
        delete_tag(uid)
        self.assertIsNone(get_tag_by_uid(uid))

if __name__ == "__main__":
    unittest.main()
