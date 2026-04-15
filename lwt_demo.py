from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from mqtt_client import SyncMqttClient, WillConfig


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_lwt_demo(host: str, port: int, topic_base: str) -> None:
    topic = f"{topic_base}/lwt/status"
    device_id = "sensor-temp-01"

    offline_payload = json.dumps(
        {
            "deviceId": device_id,
            "status": "offline",
            "source": "LWT",
            "reason": "unexpected_disconnect",
            "at": utc_now(),
        }
    )
    online_payload = json.dumps(
        {
            "deviceId": device_id,
            "status": "online",
            "source": "publisher",
            "at": utc_now(),
        }
    )

    print("\n=== DEMO LWT ===")
    print("Objetivo: broker avisar queda inesperada do dispositivo.")

    monitor = SyncMqttClient("monitor-lwt", host, port)
    device = SyncMqttClient(
        device_id,
        host,
        port,
        keepalive=2,
        will=WillConfig(topic=topic, payload=offline_payload),
    )

    try:
        monitor.connect()
        monitor.subscribe(topic)
        print(f"[monitor] inscrito em {topic}")

        device.connect()
        device.publish(topic, online_payload, qos=1, retain=False)
        print(f"[device] status online publicado: {online_payload}")

        time.sleep(1)
        print("[device] simulando falha brusca")
        device.crash()

        offline_message = monitor.wait_for_message(
            lambda message: message.topic == topic and '"status": "offline"' in message.payload,
            timeout=8,
        )
        print(f"[monitor] LWT recebido: {offline_message.payload}")
        print("Resultado: outros clientes descobrem queda sem polling.")
    finally:
        monitor.close()
