# terraform/variables.tf

variable "aws_region" {
  description = "AWS region to deploy resources."
  type        = string
  
  # Defaulting to us-east-1 (N. Virginia) for optimal FinOps/cost-efficiency during CI/CD testing.
  # Note: For a production Fintech deployment in Australia (e.g., Stake/Easygo), 
  # this MUST be overridden to 'ap-southeast-2' (Sydney) or 'ap-southeast-4' (Melbourne) 
  # to satisfy strict sub-millisecond latency requirements and data sovereignty laws.
  default     = "us-east-1" 
}