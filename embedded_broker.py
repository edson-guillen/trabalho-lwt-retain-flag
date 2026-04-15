from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field

from amqtt.broker import Broker


@dataclass
class EmbeddedBroker:
    host: str = "127.0.0.1"
    port: int = 18883
    _thread: threading.Thread | None = field(init=False, default=None)
    _loop: asyncio.AbstractEventLoop | None = field(init=False, default=None)
    _stop_event: asyncio.Event | None = field(init=False, default=None)
    _ready_event: threading.Event = field(init=False, default_factory=threading.Event)
    _broker: Broker | None = field(init=False, default=None)
    _error: BaseException | None = field(init=False, default=None)

    @property
    def url(self) -> str:
        return f"mqtt://{self.host}:{self.port}"

    @property
    def config(self) -> dict:
        return {
            "listeners": {
                "default": {
                    "type": "tcp",
                    "bind": f"{self.host}:{self.port}",
                }
            },
            "plugins": {
                "amqtt.plugins.authentication.AnonymousAuthPlugin": {
                    "allow_anonymous": True,
                },
                "amqtt.plugins.sys.broker.BrokerSysPlugin": {
                    "sys_interval": 0,
                },
            },
        }

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._ready_event.clear()
        self._error = None
        self._thread = threading.Thread(target=self._run, daemon=True, name="embedded-mqtt-broker")
        self._thread.start()

        if not self._ready_event.wait(timeout=10):
            raise TimeoutError("Broker local nao iniciou no tempo esperado.")

        if self._error is not None:
            raise RuntimeError("Falha ao iniciar broker local.") from self._error

    def stop(self) -> None:
        if not self._thread:
            return

        if self._loop and self._stop_event:
            self._loop.call_soon_threadsafe(self._stop_event.set)

        self._thread.join(timeout=10)
        self._thread = None

    def _run(self) -> None:
        asyncio.run(self._main())

    async def _main(self) -> None:
        try:
            self._loop = asyncio.get_running_loop()
            self._stop_event = asyncio.Event()
            self._broker = Broker(self.config)
            await self._broker.start()
            self._ready_event.set()
            await self._stop_event.wait()
        except BaseException as error:
            self._error = error
            self._ready_event.set()
        finally:
            if self._broker is not None:
                await self._broker.shutdown()
