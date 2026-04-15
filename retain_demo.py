from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from mqtt_client import SyncMqttClient


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_retain_demo(host: str, port: int, topic_base: str) -> None:
    topic = f"{topic_base}/retain/last-reading"
    retained_payload = json.dumps(
        {
            "deviceId": "sensor-temp-01",
            "temperature": 23.7,
            "unit": "C",
            "source": "retained_message",
            "at": utc_now(),
        }
    )

    print("\n=== DEMO RETAIN FLAG ===")
    print("Objetivo: novo inscrito receber ultimo estado imediatamente.")

    publisher = SyncMqttClient("publisher-retain", host, port)
    late_subscriber = SyncMqttClient("late-subscriber", host, port)

    try:
        publisher.connect()
        publisher.publish(topic, retained_payload, qos=1, retain=True)
        print(f"[publisher] mensagem retida publicada: {retained_payload}")

        time.sleep(0.5)

        late_subscriber.connect()
        late_subscriber.subscribe(topic)
        print(f"[late-subscriber] inscrito em {topic}")

        retained_message = late_subscriber.wait_for_message(
            lambda message: message.topic == topic,
            timeout=5,
        )
        print(f"[late-subscriber] recebeu ao conectar: {retained_message.payload}")
        print(f"[late-subscriber] flag retain no pacote: {retained_message.retain}")
        print("Resultado: cliente novo inicia com ultimo valor conhecido.")

        publisher.publish(topic, "", qos=1, retain=True)
        print("[publisher] mensagem retida limpa para nao poluir prox execucao")
    finally:
        late_subscriber.close()
        publisher.close()
