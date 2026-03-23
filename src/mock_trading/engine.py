# src/mock_trading/engine.py

import os
import json
import time
import uuid
import random
import logging
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MockTradingEngine")

class MockTradingEngine:
    def __init__(self, stream_name: str, region_name: str = "us-east-1"):
        self.stream_name = stream_name
        self.anomaly_rate = 0.05  
        self.gateways = ["STAKE_PAY", "STRIPE", "INTERNAL_LEDGER"]
        
        # Enterprise Best Practice: Dynamic Endpoint Injection
        # If LOCALSTACK_ENDPOINT is set, route traffic to LocalStack. 
        # Otherwise, route to real AWS.
        local_endpoint = os.getenv("LOCALSTACK_ENDPOINT")
        
        if local_endpoint:
            logger.info(f"Initializing Kinesis client routing to LocalStack at {local_endpoint}")
            self.kinesis_client = boto3.client(
                'kinesis', 
                region_name=region_name,
                endpoint_url=local_endpoint,
                # Dummy credentials required by boto3 when testing locally
                aws_access_key_id="test",
                aws_secret_access_key="test"
            )
        else:
            logger.info("Initializing Kinesis client routing to PRODUCTION AWS.")
            self.kinesis_client = boto3.client('kinesis', region_name=region_name)

    def _generate_normal_trade(self) -> dict:
        return {
            "transaction_id": str(uuid.uuid4()),
            "user_id": f"USR_{random.randint(1000, 9999)}",
            "amount": round(random.uniform(10.0, 5000.0), 2),
            "currency": "USD",
            "gateway": random.choice(self.gateways),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "COMPLETED"
        }

    def _inject_anomaly(self, trade: dict) -> dict:
        anomaly_type = random.choice(["AMOUNT_MISMATCH", "CURRENCY_SLIPPAGE", "MISSING_GATEWAY"])
        if anomaly_type == "AMOUNT_MISMATCH":
            trade["amount"] = round(trade["amount"] * 0.99, 2)
            trade["anomaly_tag"] = anomaly_type
        elif anomaly_type == "CURRENCY_SLIPPAGE":
            trade["currency"] = "AUD" 
            trade["anomaly_tag"] = anomaly_type
        elif anomaly_type == "MISSING_GATEWAY":
            trade["gateway"] = None 
            trade["anomaly_tag"] = anomaly_type
        return trade

    def run(self, num_records: int = 100):
        logger.info(f"Starting engine. Target: {num_records} records to '{self.stream_name}'.")
        success_count = 0
        
        for _ in range(num_records):
            trade = self._generate_normal_trade()
            if random.random() < self.anomaly_rate:
                trade = self._inject_anomaly(trade)
                logger.warning(f"Injected Anomaly: {trade['transaction_id']} -> {trade.get('anomaly_tag')}")

            try:
                self.kinesis_client.put_record(
                    StreamName=self.stream_name,
                    Data=json.dumps(trade),
                    PartitionKey=trade["user_id"] 
                )
                success_count += 1
            except ClientError as e:
                logger.error(f"Failed to push record: {e}")
            
            time.sleep(0.05) 

        logger.info(f"Engine stopped. Pushed {success_count}/{num_records} records.")

if __name__ == "__main__":
    ENGINE = MockTradingEngine(stream_name="auto-recon-transaction-stream")
    ENGINE.run(num_records=50)