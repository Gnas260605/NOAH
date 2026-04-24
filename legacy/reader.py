import csv, pika, json, time, hashlib
import os
import random
import socket

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')

def get_connection():
    while True:
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        except (pika.exceptions.AMQPConnectionError, socket.error):
            time.sleep(5)

def generate_id(data):
    relevant = {
        "user_id": data.get("user_id"),
        "product_id": data.get("product_id"),
        "quantity": data.get("quantity"),
        "total_price": data.get("total_price")
    }
    row_str = json.dumps(relevant, sort_keys=True)
    return hashlib.sha256(row_str.encode()).hexdigest()[:16]

def run_legacy_producer():
    conn = get_connection()
    ch = conn.channel()
    ch.queue_declare(queue='orders', durable=True, arguments={
        'x-dead-letter-exchange': 'dlx',
        'x-dead-letter-routing-key': 'failed_orders'
    })

    csv_path = "inventory.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    count = 0
    dirty_count = 0
    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    # 1. Extraction
                    raw_pid = r.get("product_id") or r.get("id")
                    raw_qty = r.get("quantity") or r.get("amount")
                    
                    if not raw_pid or not raw_qty:
                        continue
                        
                    p_id = int(raw_pid)
                    qty = int(float(raw_qty))
                    
                    # 2. Assignment Strategy: NEGATIVE_NUMBERS Handling
                    if qty < 0:
                        print(f"[Module 1] DIRTY DATA: Negative Qty ({qty}) detected for Product {p_id}. Correcting...")
                        qty = abs(qty)
                        dirty_count += 1
                    
                    price = float(qty * 125000) # Mock logic
                    
                    data = {
                        "user_id": random.randint(900, 999),
                        "product_id": p_id,
                        "quantity": qty,
                        "total_price": price
                    }
                    data["message_id"] = generate_id(data)

                    ch.basic_publish(
                        exchange='',
                        routing_key='orders',
                        body=json.dumps(data),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    count += 1
                except Exception as e:
                    # Satisfying requirement: MUST use try-except to skip/fix errors
                    print(f"[Module 1] Skipping invalid row: {e}")
                    continue
                    
        print(f"Ingestion Finished: {count} total, {dirty_count} corrected.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_legacy_producer()