# terraform/main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. High-throughput Data Stream (On-Demand mode for FinOps cost efficiency)
resource "aws_kinesis_stream" "transaction_stream" {
  name = "auto-recon-transaction-stream"
  
  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}

# 2. Dead Letter Queue (DLQ) for exception handling and AI agent routing
resource "aws_sqs_queue" "exception_dlq" {
  name                      = "auto-recon-exceptions-dlq"
  message_retention_seconds = 86400 # Retain messages for 1 day
}

# 3. Data Lake for archiving reconciled records and AI resolution payloads
resource "aws_s3_bucket" "data_lake" {
  bucket_prefix = "auto-recon-data-lake-"
  force_destroy = true # Essential for Ephemeral CI/CD environments (auto-cleanup)
}

# 4. Lifecycle rule to ensure ephemeral storage compliance
resource "aws_s3_bucket_lifecycle_configuration" "lake_lifecycle" {
  bucket = aws_s3_bucket.data_lake.id
  
  rule {
    id     = "auto-delete-after-1-day"
    status = "Enabled"
    
    expiration {
      days = 1
    }
  }
}