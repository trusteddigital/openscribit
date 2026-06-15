# Firmware binaries

Place release/build firmware binaries here before packaging:

- `ScribitESP.ino.bin` for ESP32 OTA.
- `MK4duo.ino.bin` for SAMD21 OTA (`espota.py -c`).
- `ScribitESP.ino.partitions.bin` for partition OTA (`espota.py -s`).

The desktop app validates that each file exists and is non-empty before flashing. Docker is only needed if you rebuild firmware from source.
