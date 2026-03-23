# localstack-init/init-aws.sh
#!/bin/bash
echo " Initializing LocalStack AWS Resources..."

# Create Kinesis Stream
awslocal kinesis create-stream --stream-name auto-recon-transaction-stream --shard-count 1
echo "Kinesis Stream 'auto-recon-transaction-stream' created."

# Create SQS Dead Letter Queue
awslocal sqs create-queue --queue-name auto-recon-exceptions-dlq
echo "SQS Queue 'auto-recon-exceptions-dlq' created."

echo " All local AWS infrastructure provisioned successfully!"