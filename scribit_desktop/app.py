from __future__ import annotations

import logging
import sys
import threading
import uuid
import webbrowser
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from firmware_flash import flash_firmware
from image_to_gcode import convert_image_to_gcode
from scribit_client import ScribitClient, DEFAULT_ROBOT_IP, guess_host_ip_for

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
LOG = logging.getLogger("scribit_desktop")
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
app = FastAPI(title="Scribit Desktop")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
SESSIONS: dict[str, dict[str, str | int]] = {}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/api/test")
def test(robot_ip: str = Form(DEFAULT_ROBOT_IP)) -> dict:
    return ScribitClient(robot_ip=robot_ip).test_connection()


@app.post("/api/wifi")
def wifi(ssid: str = Form(...), password: str = Form(...)) -> dict:
    return ScribitClient().configure_wifi(ssid, password)


@app.post("/api/convert")
async def convert(file: UploadFile = File(...), width_mm: float = Form(180.0), height_mm: float = Form(180.0)) -> JSONResponse:
    data = await file.read()
    try:
        result = convert_image_to_gcode(data, file.filename or "image.png", width_mm, height_mm)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    token = uuid.uuid4().hex
    SESSIONS[token] = {"gcode": result.gcode, "path_count": result.path_count, "gcode_size_bytes": result.gcode_size_bytes}
    return JSONResponse({"token": token, "preview_svg": result.preview_svg, "path_count": result.path_count, "gcode_size_bytes": result.gcode_size_bytes, "warning": result.warning})


@app.post("/api/send")
def send(token: str = Form(...), robot_ip: str = Form(DEFAULT_ROBOT_IP), robot_id: str = Form("robot"), mqtt_host: str = Form(""), host_ip: str = Form(""), suffix: str = Form("G4 P0")) -> dict:
    session = SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=404, detail="Convert an image before sending.")
    actual_host_ip = host_ip or guess_host_ip_for(robot_ip)
    client = ScribitClient(robot_ip=robot_ip, robot_id=robot_id, mqtt_host=mqtt_host or robot_ip)
    return client.send_gcode(str(session["gcode"]), actual_host_ip, suffix)


@app.get("/api/flash/{target}")
def flash(target: str, robot_ip: str = DEFAULT_ROBOT_IP) -> StreamingResponse:
    def stream():
        try:
            yield from flash_firmware(robot_ip, target)
        except Exception as exc:
            yield f"ERROR: {exc}\n"
    return StreamingResponse(stream(), media_type="text/plain")


def main() -> None:
    url = "http://127.0.0.1:8765/"
    if not getattr(sys, "frozen", False):
        LOG.info("Starting development server at %s", url)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
