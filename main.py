from __future__ import annotations

import os
from urllib.parse import urlparse

from embedded_broker import EmbeddedBroker
from lwt_demo import run_lwt_demo
from retain_demo import run_retain_demo


def resolve_broker() -> tuple[str, int, EmbeddedBroker | None, str]:
    broker_url = os.getenv("BROKER_URL")
    if broker_url:
        parsed = urlparse(broker_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 1883
        return host, port, None, broker_url

    host = os.getenv("BROKER_HOST", "127.0.0.1")
    port = int(os.getenv("BROKER_PORT", "18883"))
    broker = EmbeddedBroker(host=host, port=port)
    broker.start()
    return host, port, broker, broker.url


def main() -> None:
    topic_base = os.getenv("TOPIC_BASE", "trabalho/python/lwt-retain")
    host, port, broker, broker_url = resolve_broker()

    print("Broker alvo:", broker_url)
    print("Base topicos:", topic_base)

    try:
        run_lwt_demo(host, port, topic_base)
        run_retain_demo(host, port, topic_base)
        print("\nDemo completa.")
    finally:
        if broker is not None:
            broker.stop()


if __name__ == "__main__":
    main()
