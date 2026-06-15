from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterator

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
SOURCE_DIR = Path(__file__).resolve().parent
ESPOTA = BASE_DIR / "vendor" / "mbc-wb_2.0.0" / "tools" / "espota.py"
if not ESPOTA.exists():
    ESPOTA = SOURCE_DIR.parent / "vendor" / "mbc-wb_2.0.0" / "tools" / "espota.py"
FIRMWARE_DIR = BASE_DIR / "firmware"
OTA_PORT = 3232

TARGETS = {
    "esp32": {"file": "ScribitESP.ino.bin", "flags": []},
    "samd21": {"file": "MK4duo.ino.bin", "flags": ["-c"]},
    "partition": {"file": "ScribitESP.ino.partitions.bin", "flags": ["-s"]},
}


def firmware_path(target: str) -> Path:
    if target not in TARGETS:
        raise ValueError(f"Unknown firmware target: {target}")
    return FIRMWARE_DIR / TARGETS[target]["file"]


def build_espota_command(robot_ip: str, target: str) -> list[str]:
    fw = firmware_path(target)
    if not ESPOTA.exists():
        raise FileNotFoundError(f"espota.py not found: {ESPOTA}")
    if not fw.exists() or fw.stat().st_size == 0:
        raise FileNotFoundError(f"Firmware file is missing or empty: {fw}")
    return [sys.executable, str(ESPOTA), "-i", robot_ip, "-p", str(OTA_PORT), *TARGETS[target]["flags"], "-f", str(fw)]


def flash_firmware(robot_ip: str, target: str) -> Iterator[str]:
    if target == "partition":
        yield "WARNING: Partition flashing can change device storage layout. Continue only if you know this is required.\n"
    cmd = build_espota_command(robot_ip, target)
    yield "Running: " + " ".join(cmd) + "\n"
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    assert process.stdout is not None
    for line in process.stdout:
        yield line
    rc = process.wait()
    if rc:
        raise RuntimeError(f"espota.py exited with code {rc}")
    yield "Done.\n"
