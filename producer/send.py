"""
producer/send.py – Continuous Order Producer for Noah Retail
Sends random orders to RabbitMQ every second with resilient reconnect logic.
"""

import json
import os
import random
import socket
import time
import logging

import pika

# ── Config ────────────────────────────────────────────────────────────────────
RABBITMQ_HOST  = os.getenv("RABBITMQ_HOST",  "rabbitmq")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "orders")
SEND_INTERVAL  = float(os.getenv("SEND_INTERVAL", "1.0"))  # seconds between sends

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s producer – %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("producer")


def get_connection():
    """Block until RabbitMQ is reachable, then return (conn, channel)."""
    while True:
        try:
            log.info("Connecting to RabbitMQ at %s…", RABBITMQ_HOST)
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )
            ch = conn.channel()
            # Declare DLX so the queue can route failures properly
            ch.exchange_declare(exchange="dlx", exchange_type="direct")
            ch.queue_declare(queue="failed_orders", durable=True)
            ch.queue_bind(exchange="dlx", queue="failed_orders", routing_key="failed_orders")
            ch.queue_declare(
                queue=RABBITMQ_QUEUE,
                durable=True,
                arguments={
                    "x-dead-letter-exchange":    "dlx",
                    "x-dead-letter-routing-key": "failed_orders",
                },
            )
            log.info("Connected. Starting to produce orders every %.1fs…", SEND_INTERVAL)
            return conn, ch
        except (pika.exceptions.AMQPConnectionError, socket.error) as exc:
            log.warning("Connection failed: %s – retrying in 5s", exc)
            time.sleep(5)


def generate_order() -> dict:
    """Generate a random realistic order payload."""
    product_id = random.randint(100, 300)
    quantity   = random.randint(1, 10)
    unit_price = random.choice([50_000, 75_000, 125_000, 200_000, 350_000, 500_000])
    return {
        "message_id":  f"auto-{os.urandom(8).hex()}",
        "user_id":     random.randint(1_000, 9_999),
        "product_id":  product_id,
        "quantity":    quantity,
        "total_price": round(quantity * unit_price, 2),
        "created_at":  time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def run():
    """Main loop: connect and send one order per SEND_INTERVAL seconds."""
    conn, ch = get_connection()
    sent = 0

    while True:
        try:
            order = generate_order()
            ch.basic_publish(
                exchange="",
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(order),
                properties=pika.BasicProperties(delivery_mode=2),  # persistent
            )
            sent += 1
            log.info(
                "[#%d] Sent → Product:%d Qty:%d Price:%.0f",
                sent,
                order["product_id"],
                order["quantity"],
                order["total_price"],
            )
            time.sleep(SEND_INTERVAL)

        except (pika.exceptions.AMQPError, socket.error) as exc:
            log.warning("Connection lost: %s – reconnecting…", exc)
            conn, ch = get_connection()


if __name__ == "__main__":
    run()
