from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event
from typing import Callable

import paho.mqtt.client as mqtt


@dataclass(frozen=True)
class WillConfig:
    topic: str
    payload: str
    qos: int = 1
    retain: bool = False


@dataclass(frozen=True)
class ReceivedMessage:
    topic: str
    payload: str
    retain: bool


class SyncMqttClient:
    def __init__(
        self,
        client_id: str,
        host: str,
        port: int,
        *,
        keepalive: int = 10,
        will: WillConfig | None = None,
    ) -> None:
        self.client_id = client_id
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self._message_queue: Queue[ReceivedMessage] = Queue()
        self._connected = Event()
        self._subscribed = Event()
        self._subscribe_mid: int | None = None

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv311,
            reconnect_on_failure=False,
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_subscribe = self._on_subscribe

        if will is not None:
            self._client.will_set(
                will.topic,
                payload=will.payload,
                qos=will.qos,
                retain=will.retain,
            )

    def connect(self) -> None:
        self._client.connect(self.host, self.port, keepalive=self.keepalive)
        self._client.loop_start()

        if not self._connected.wait(timeout=5):
            raise TimeoutError(f"{self.client_id}: timeout na conexao MQTT.")

        print(f"[{self.client_id}] conectado")

    def subscribe(self, topic: str, qos: int = 1) -> None:
        self._subscribed.clear()
        result, mid = self._client.subscribe(topic, qos=qos)
        if result != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"{self.client_id}: erro ao assinar topico {topic}. rc={result}")

        self._subscribe_mid = mid
        if not self._subscribed.wait(timeout=5):
            raise TimeoutError(f"{self.client_id}: timeout na inscricao de {topic}.")

    def publish(self, topic: str, payload: str, *, qos: int = 1, retain: bool = False) -> None:
        info = self._client.publish(topic, payload=payload, qos=qos, retain=retain)
        info.wait_for_publish(timeout=5)
        if not info.is_published():
            raise TimeoutError(f"{self.client_id}: timeout publicando em {topic}.")

    def wait_for_message(
        self,
        matcher: Callable[[ReceivedMessage], bool],
        *,
        timeout: float = 5.0,
    ) -> ReceivedMessage:
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            try:
                message = self._message_queue.get(timeout=max(remaining, 0.05))
            except Empty:
                continue

            if matcher(message):
                return message

        raise TimeoutError(f"{self.client_id}: timeout aguardando mensagem MQTT.")

    def crash(self) -> None:
        sock = self._client.socket()
        if sock is None:
            raise RuntimeError(f"{self.client_id}: socket MQTT indisponivel para simular falha.")

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        sock.close()
        self._client.loop_stop()

    def close(self) -> None:
        try:
            self._client.disconnect()
        except OSError:
            pass
        finally:
            self._client.loop_stop()

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code != 0:
            raise RuntimeError(f"{self.client_id}: conexao recusada. rc={reason_code}")

        self._connected.set()

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties) -> None:
        if self._subscribe_mid == mid:
            self._subscribed.set()

    def _on_message(self, client, userdata, message) -> None:
        self._message_queue.put(
            ReceivedMessage(
                topic=message.topic,
                payload=message.payload.decode("utf-8"),
                retain=message.retain,
            )
        )
