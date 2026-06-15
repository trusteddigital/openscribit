from __future__ import annotations

import logging
import socket
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests
import paho.mqtt.client as mqtt

LOG = logging.getLogger("scribit_desktop.client")
DEFAULT_ROBOT_IP = "192.168.240.1"
WIFI_CONFIG_URL = "http://192.168.240.1:8888/"


class ScribitClient:
    def __init__(self, robot_ip: str = DEFAULT_ROBOT_IP, robot_id: str = "robot", mqtt_host: str | None = None, mqtt_port: int = 1883, mqtt_user: str = "scribit", mqtt_password: str = "scribit") -> None:
        self.robot_ip = robot_ip
        self.robot_id = robot_id
        self.mqtt_host = mqtt_host or robot_ip
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password

    def test_connection(self) -> dict:
        url = f"http://{self.robot_ip}:8888/"
        LOG.info("GET %s", url)
        response = requests.get(url, timeout=5)
        return {"ok": response.ok, "status_code": response.status_code, "text": response.text[:500]}

    def configure_wifi(self, ssid: str, password: str) -> dict:
        payload = {"ssid": ssid, "password": password}
        LOG.info("POST %s json keys=%s", WIFI_CONFIG_URL, list(payload))
        response = requests.post(WIFI_CONFIG_URL, json=payload, timeout=15)
        return {"ok": response.ok, "status_code": response.status_code, "text": response.text[:1000]}

    def publish_mqtt(self, command: str, payload: str) -> None:
        topic = f"tin/{self.robot_id}/{command}"
        LOG.info("MQTT publish host=%s:%s topic=%s bytes=%d", self.mqtt_host, self.mqtt_port, topic, len(payload.encode()))
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.mqtt_user or self.mqtt_password:
            client.username_pw_set(self.mqtt_user, self.mqtt_password)
        client.connect(self.mqtt_host, self.mqtt_port, keepalive=30)
        info = client.publish(topic, payload, qos=1)
        info.wait_for_publish(timeout=10)
        client.disconnect()
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed: {mqtt.error_string(info.rc)}")

    def send_gcode(self, gcode: str, host_ip: str, suffix: str = "G4 P0") -> dict:
        """Serve G-code on local HTTP port 80 and send the confirmed MQTT print command.

        TODO: Verify final suffix and calibration expectations on real hardware.
        The firmware rejects URLs containing a port, so this uses port 80.
        """
        tmp = tempfile.TemporaryDirectory()
        directory = Path(tmp.name)
        path = directory / "drawing.gcode"
        path.write_text(gcode, encoding="utf-8")

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(directory), **kwargs)

        httpd = ThreadingHTTPServer(("0.0.0.0", 80), Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        payload = f"http://{host_ip}/drawing.gcode;{suffix}"
        try:
            self.publish_mqtt("status", "{}")
            self.publish_mqtt("print", payload)
            return {"ok": True, "payload": payload, "note": "HTTP server started on port 80 for robot download."}
        finally:
            # Keep server briefly available; production should track download completion via MQTT status.
            threading.Timer(120, lambda: (httpd.shutdown(), tmp.cleanup())).start()


def guess_host_ip_for(robot_ip: str) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect((robot_ip, 80))
            return s.getsockname()[0]
        except OSError:
            return "192.168.240.2"
