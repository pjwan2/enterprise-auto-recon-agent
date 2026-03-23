# src/recon_processor/consumer.py

import os
import json
import time
import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StreamProcessor")

class ReconStreamProcessor:
    def __init__(self, stream_name: str, dlq_name: str, region_name: str = "us-east-1"):
        self.stream_name = stream_name
        self.dlq_name = dlq_name
        
        # Enterprise Best Practice: Dynamic Endpoint Injection
        local_endpoint = os.getenv("LOCALSTACK_ENDPOINT")
        
        client_kwargs = {
            "region_name": region_name
        }
        if local_endpoint:
            client_kwargs["endpoint_url"] = local_endpoint
            client_kwargs["aws_access_key_id"] = "test"
            client_kwargs["aws_secret_access_key"] = "test"
            logger.info(f"Connecting to LocalStack at {local_endpoint}")

        self.kinesis = boto3.client('kinesis', **client_kwargs)
        self.sqs = boto3.client('sqs', **client_kwargs)
        
        # Resolve SQS Queue URL
        try:
            response = self.sqs.get_queue_url(QueueName=self.dlq_name)
            self.dlq_url = response['QueueUrl']
            logger.info(f"Resolved DLQ URL: {self.dlq_url}")
        except ClientError as e:
            logger.error(f"Failed to find SQS Queue '{self.dlq_name}'. Did you create it?")
            raise e

    def _route_to_dlq(self, record: dict, reason: str):
        """Routes bad records to the Dead Letter Queue for AI Agent processing."""
        payload = {
            "transaction_data": record,
            "failure_reason": reason,
            "timestamp": time.time()
        }
        try:
            self.sqs.send_message(
                QueueUrl=self.dlq_url,
                MessageBody=json.dumps(payload)
            )
            logger.error(f"🚨 SENT TO DLQ: Transaction {record.get('transaction_id')} - Reason: {reason}")
        except ClientError as e:
            logger.error(f"Failed to send to DLQ: {e}")

    def process_stream(self):
        """Polls the Kinesis stream and processes records in near real-time."""
        logger.info(f"Starting real-time consumer for stream: {self.stream_name}")
        
        # 1. Get the Shard ID (Assuming 1 shard for this MVP)
        stream_info = self.kinesis.describe_stream(StreamName=self.stream_name)
        shard_id = stream_info['StreamDescription']['Shards'][0]['ShardId']
        
        # 2. Get the initial Shard Iterator (TRIM_HORIZON means read from the oldest available record)
        iterator_resp = self.kinesis.get_shard_iterator(
            StreamName=self.stream_name,
            ShardId=shard_id,
            ShardIteratorType='TRIM_HORIZON'
        )
        shard_iterator = iterator_resp['ShardIterator']
        
        logger.info("Listening for incoming transactions...")
        
        # 3. Continuous polling loop
        while shard_iterator:
            response = self.kinesis.get_records(ShardIterator=shard_iterator, Limit=100)
            records = response.get('Records', [])
            
            for raw_record in records:
                # Kinesis data is base64 encoded, boto3 decodes it to bytes automatically
                data_str = raw_record['Data'].decode('utf-8')
                trade = json.loads(data_str)
                
                # --- The Reconciliation Rules Engine ---
                # This simulates comparing internal ledger vs gateway data
                if trade.get('gateway') is None:
                    self._route_to_dlq(trade, "FATAL: Missing Payment Gateway ID")
                elif trade.get('currency') != 'USD':
                    self._route_to_dlq(trade, f"WARNING: Foreign Currency Slippage Detected ({trade.get('currency')})")
                elif trade.get('anomaly_tag') == 'AMOUNT_MISMATCH':
                    # In reality, you'd calculate this by querying the gateway API. 
                    # We trigger off our injected tag for the MVP.
                    self._route_to_dlq(trade, "ERROR: Ledger amount does not match Gateway amount")
                else:
                    logger.info(f"✅ SUCCESS: Transaction {trade['transaction_id']} perfectly reconciled.")
            
            # Get the next iterator
            shard_iterator = response.get('NextShardIterator')
            
            # AWS best practice: Sleep to avoid exceeding Kinesis Read API limits
            time.sleep(1) 

if __name__ == "__main__":
    CONSUMER = ReconStreamProcessor(
        stream_name="auto-recon-transaction-stream",
        dlq_name="auto-recon-exceptions-dlq"
    )
    CONSUMER.process_stream()