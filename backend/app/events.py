import json
from confluent_kafka import Producer
from .config import get_settings

settings = get_settings()

def _producer() -> Producer:
    return Producer({"bootstrap.servers": settings.kafka_bootstrap_servers, "client.id": "khmerlive-api", "enable.idempotence": True, "acks": "all"})

def publish(topic: str, event: dict, key: str | None = None, timeout: float = 10.0) -> None:
    p = _producer()
    delivery_error = []
    def callback(err, _msg):
        if err is not None:
            delivery_error.append(err)
    p.produce(topic, key=key, value=json.dumps(event, ensure_ascii=False).encode("utf-8"), callback=callback)
    remaining = p.flush(timeout)
    if delivery_error or remaining:
        raise RuntimeError(f"Kafka delivery failed: {delivery_error[0] if delivery_error else 'flush timeout'}")

def healthy() -> bool:
    try:
        return bool(_producer().list_topics(timeout=3).brokers)
    except Exception:
        return False
