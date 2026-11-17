import json

from confluent_kafka import Producer

from .config import get_settings

settings = get_settings()


def client_config(client_id: str) -> dict:
    config = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "client.id": client_id,
        "security.protocol": settings.kafka_security_protocol,
    }
    if settings.kafka_security_protocol.upper() in {"SSL", "SASL_SSL"}:
        config["ssl.ca.location"] = settings.kafka_ssl_ca_location
        config["enable.ssl.certificate.verification"] = True
    return config


def _producer() -> Producer:
    config = client_config("khmerlive-api")
    config.update({"enable.idempotence": True, "acks": "all"})
    return Producer(config)


def publish(topic: str, event: dict, key: str | None = None, timeout: float = 10.0) -> None:
    p = _producer()
    delivery_error = []

    def callback(err, _msg):
        if err is not None:
            delivery_error.append(err)

    p.produce(
        topic,
        key=key,
        value=json.dumps(event, ensure_ascii=False).encode("utf-8"),
        callback=callback,
    )
    remaining = p.flush(timeout)
    if delivery_error or remaining:
        raise RuntimeError(
            f"Kafka delivery failed: {delivery_error[0] if delivery_error else 'flush timeout'}"
        )


def healthy() -> bool:
    try:
        return bool(_producer().list_topics(timeout=3).brokers)
    except Exception:
        return False
