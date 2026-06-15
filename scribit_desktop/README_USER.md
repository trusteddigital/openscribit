# Scribit Desktop user guide

1. Turn on Scribit and wait for its Wi-Fi access point.
2. Connect this Windows computer to the Scribit AP. The default AP password is `ScribItAP314`.
3. Run `ScribitDesktop.exe`; it opens a local browser page.
4. Keep the default robot IP `192.168.240.1` unless you know the robot is on another address.
5. Flash firmware only if needed. ESP32, SAMD21, and partition flashing use OTA port `3232`; partition flashing is advanced.
6. Configure Wi-Fi if desired by entering your network SSID and password. The app sends the confirmed JSON Wi-Fi form to `http://192.168.240.1:8888/`.
7. Upload a PNG, JPG, JPEG, or WEBP image.
8. Preview the generated line-art. Check the path count and G-code size; files over 5 MB may be unreliable.
9. Click **Send drawing** only when the robot, wall, cables, and pen are ready.

Emergency stop: unplug Scribit power if motion is unsafe.
