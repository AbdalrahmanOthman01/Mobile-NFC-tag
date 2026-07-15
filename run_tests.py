import sys
import unittest

# Import the test suites
from tests.test_database import TestEncryptedDatabase
from tests.test_nfc_features import TestNFCFeatures

def run_suite():
    print("Starting secure unit tests runner...", flush=True)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestEncryptedDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestNFCFeatures))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print(f"\nTests Completed. Success: {result.wasSuccessful()}", flush=True)
    if not result.wasSuccessful():
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_suite()
