[app]

# (str) Title of your application
title = NFC Vault & Badge

# (str) Package name
package.name = nfcvault

# (str) Package domain (needed for android packaging)
package.domain = org.example

# (str) Source code directory
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,xml,db

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0,kivymd==1.2.0,cryptography,openssl,pyjnius,plyer

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
# services = securebadge:nfc/java_hce/SecureBadgeService.py

#
# Android specific
#

# (bool) Indicate if the application should be monitor for keepalive
# android.keepalive = False

# (list) Android permissions to request
android.permissions = NFC, WAKE_LOCK, INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 26b

# (bool) Use --private data directory (True) or public (False)
android.private_storage = True
android.accept_sdk_license = True
android.extra_manifest_application_xml = %(source.dir)s/nfc/manifest_additions.xml

# (list) Android additional Java source dirs to compile
# This is where we put our custom HostApduService.java class
android.add_srcs = nfc/java_hce

# (list) Android additional resources to add (e.g. apduservice.xml)
# Maps local res files to Android package resources
android.add_resources = nfc/java_hce/res

# (str) Android entry point, default is to use start.py of python-for-android
# android.entrypoint = org.kivy.android.PythonActivity

# (list) Pattern to exclude from the resources
# android.exclude_resources = 

# (str) Bootstrap to use for android build
# android.bootstrap = sdl2

# (list) Gradle dependencies
# android.gradle_dependencies = 

# (list) Packaging options to pass to gradle
# android.packaging_options = 

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 1

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0
