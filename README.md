# 🏦 Enterprise FinOps AI Agent: Real-Time Payment Reconciliation

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)
![AWS](https://img.shields.io/badge/AWS-Kinesis%20%7C%20SQS-FF9900.svg)
![AI](https://img.shields.io/badge/GenAI-LangGraph%20%7C%20Gemini-4285F4.svg)
![Status](https://img.shields.io/badge/Status-MVP_Ready-brightgreen.svg)

## 📖 Executive Summary
In modern Tier-1 financial systems (e.g., payment gateways, digital wallets), T+1 batch reconciliation is no longer sufficient. This project demonstrates an **Event-Driven, AI-Powered FinOps Architecture** designed to process streaming financial transactions in real-time, instantly detect ledger anomalies, and autonomously resolve discrepancies using a deterministic Agentic Workflow (`LangGraph`). 

Crucially, it addresses the primary risk of GenAI in finance—**Hallucinations and Unauthorized Writes**—by enforcing strict schema boundaries (`Pydantic`) and operating in a **Shadow Mode** sandbox, routing high-risk fixes to a **Human-in-the-Loop (HITL)** Streamlit Command Center.

## 🏗️ System Architecture

<img width="1196" height="998" alt="image" src="https://github.com/user-attachments/assets/ce21d78e-6dec-4a9c-aab3-8d82daee098f" />


✨ Core Engineering Features
Event-Driven Streaming: Sub-second transaction processing using AWS Kinesis (simulated via LocalStack).

Poison Pill Mitigation: SQS Dead Letter Queue (DLQ) pattern isolates malformed anomalies, ensuring the primary stream shard is never blocked.

Agentic State Machine (LangGraph): Moves beyond stateless prompts. The workflow is modeled as a Directed Acyclic Graph (DAG) for deterministic, multi-step LLM reasoning.

Zero-Hallucination Guardrails: AI-generated payloads are strictly validated against Pydantic schemas before progressing to the execution node.

Shadow Mode Execution: AI securely diagnoses the root cause but is cryptographically blocked from executing UPDATE_LEDGER commands. It routes the proposed fix to the HITL dashboard.

FinOps Optimization: Dynamically defaults to gemini-2.5-flash for high-throughput, low-cost anomaly resolution, avoiding expensive models for routine deterministic tasks.

🚀 Quick Start (Local Deployment)
This project is fully containerized and uses LocalStack to mock AWS infrastructure.

Setup
Clone the repository:

Bash
git clone [https://github.com/yourusername/enterprise-auto-recon.git](https://github.com/yourusername/enterprise-auto-recon.git)
cd enterprise-auto-recon
Create a .env file in the root directory:

Code snippet
GOOGLE_API_KEY=your_gemini_api_key_here
LOCALSTACK_ENDPOINT=http://localstack:4566
EXECUTION_MODE=SHADOW
Boot the microservices cluster and provision AWS resources:

Bash
docker-compose up -d --build
Open the FinOps Command Center (HITL Dashboard):
**http://localhost:8501**

Simulating Financial Anomalies
To trigger the AI Agent, inject a batch of transactions (including intentional anomalies) into the Kinesis stream:

Bash
docker-compose restart mock-trading-engine
Watch the AI Agent intercept the anomaly in real-time via structured logs:

Bash
docker-compose logs -f ai-agent
(You will see the critical security log: [SHADOW MODE] Fix generated for XXX but BLOCKED from Production Ledger. The anomaly will then appear on your Streamlit Dashboard.)

⚖️ Architecture Decisions & Trade-offs
Building a financial-grade reconciliation system involves strict trade-offs:

1 Kinesis Polling vs. Enhanced Fan-Out (EFO):

Current MVP: Uses standard HTTP polling for simplicity.

Production: Will utilize AWS Lambda Event Source Mapping or KCL with EFO for push-based, sub-50ms latency and horizontal auto-scaling.

2 Exactly-Once Processing & Idempotency:

To prevent duplicate ledger updates during network retries, the architecture incorporates a DynamoDB Idempotency Table. The consumer leverages DynamoDB Conditional Writes locking the transaction_id before processing.

3 LangGraph vs. Vanilla LLM Calls:

Standard LLM API calls are stateless. By using LangGraph, we maintain an AgentState. If a container crashes, the state can be recovered via a Checkpointer (PostgreSQL), ensuring no financial investigation is left hanging.

🛡️ Production Governance & Non-Functional Requirements (NFRs)
To bridge the gap between a functional MVP and a Tier-1 FinTech production system, the following guardrails are designed into the target architecture:

1 Enterprise Security: Strict IAM roles separate the Consumer's read-only Kinesis access from the Agent's SQS write access. All queues are encrypted via AWS KMS. LLM API keys are injected via AWS Secrets Manager.

2 Metrics-Driven Observability: CloudWatch alarms trigger PagerDuty incidents if the SQS DLQ depth exceeds safety thresholds (indicating a potential systemic anomaly or LLM degradation).

3 LLMOps & Rollout Strategy: The AI Agent will run exclusively in Shadow Mode for the first 3 months—generating fixes alongside human auditors but executing nothing—until a 99.9% accuracy benchmark is met.



🔮 Phase 2: Production Readiness & Persistence (Future Enhancements)
While the current architecture successfully demonstrates the core real-time streaming and AI reasoning loop using an append-only JSONL event log (MVP), deploying this to a Tier-1 financial production environment requires the following persistence upgrades:

1 Relational Ledger Persistence (PostgreSQL / AWS RDS)

Replace the local .jsonl sink with a PostgreSQL database via SQLAlchemy.

Introduce ACID-compliant transactions to ensure the AI Agent's UPDATE_LEDGER commands are committed idempotently.

2 NoSQL Audit Trail (AWS DynamoDB)

Store the raw historical LLM reasoning traces (prompts, confidence scores, and raw payloads) in DynamoDB for high-throughput, unstructured compliance auditing.

3 Frontend State Management

Decouple the Streamlit dashboard into a standard React/Next.js frontend with a FastAPI backend, enabling role-based access control (RBAC) for the human-in-the-loop auditors.
