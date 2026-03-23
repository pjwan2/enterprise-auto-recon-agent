# 🏦 Enterprise FinOps AI Agent: Real-Time Payment Reconciliation

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)
![AWS](https://img.shields.io/badge/AWS-Kinesis%20%7C%20SQS-FF9900.svg)
![AI](https://img.shields.io/badge/GenAI-LangGraph%20%7C%20Gemini-4285F4.svg)
![Status](https://img.shields.io/badge/Status-MVP_Ready-brightgreen.svg)

## 📖 Executive Summary
In modern financial systems (e.g., payment gateways, digital wallets), T+1 batch reconciliation is no longer sufficient. This project demonstrates an **Event-Driven, AI-Powered FinOps Architecture** designed to process streaming financial transactions in real-time, instantly detect ledger anomalies, and autonomously resolve discrepancies using a deterministic Agentic Workflow (LangGraph). 

It features a **Human-in-the-Loop (HITL)** dashboard for auditing, ensuring that AI operates safely within strict financial compliance boundaries.

## 🏗️ System Architecture

<img width="898" height="568" alt="Architecture Diagram" src="https://github.com/user-attachments/assets/253f0e5a-ecf8-4a0e-b7f1-884a3b4cd82f" />

## ✨ Core Enterprise Features

* **Real-Time Streaming:** Simulates high-throughput financial data ingestion using AWS Kinesis (via LocalStack).
* **Poison Pill Mitigation:** Implements a Dead Letter Queue (AWS SQS) pattern to isolate malformed or anomalous transactions without blocking the primary stream shard.
* **Agentic State Machine:** Utilizes `LangGraph` to orchestrate multi-step LLM reasoning, ensuring deterministic outputs via Pydantic schemas.
* **Cost-Optimized AI (FinOps):** Dynamically defaults to `gemini-2.5-flash` for high-speed, low-cost anomaly resolution, avoiding expensive "Pro" models for routine deterministic tasks.
* **Human-in-the-Loop (HITL):** A Streamlit-based Command Center for financial auditors to manually review low-confidence AI decisions.
* **Production-Grade Resilience:**
  * **Structured JSON Logging:** Fully integrated `pythonjsonlogger` for direct ingestion into Datadog/Splunk/ELK.
  * **Graceful Shutdown:** `SIGTERM`/`SIGINT` signal catching ensures in-flight transactions are completely processed before container termination, preventing data loss.

## 🚀 Quick Start (Local Deployment)

This project is fully containerized. You do not need an AWS account; it uses LocalStack to mock AWS infrastructure.

### Prerequisites
* Docker & Docker Compose
* A Google Gemini API Key

### Setup
1. Clone the repository and navigate to the root directory.
2. Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   LOCALSTACK_ENDPOINT=http://localstack:4566
3. Build and launch the microservices cluster: docker-compose up -d --build
4. Access the FinOps Command Center (HITL Dashboard) at:  http://localhost:8501


🔮 Phase 2: Production Readiness & Persistence (Future Enhancements)
While the current architecture successfully demonstrates the core real-time streaming and AI reasoning loop using an append-only JSONL event log (MVP), deploying this to a Tier-1 financial production environment requires the following persistence upgrades:

Relational Ledger Persistence (PostgreSQL / AWS RDS)

Replace the local .jsonl sink with a PostgreSQL database via SQLAlchemy.

Introduce ACID-compliant transactions to ensure the AI Agent's UPDATE_LEDGER commands are committed idempotently.

NoSQL Audit Trail (AWS DynamoDB)

Store the raw historical LLM reasoning traces (prompts, confidence scores, and raw payloads) in DynamoDB for high-throughput, unstructured compliance auditing.

Frontend State Management

Decouple the Streamlit dashboard into a standard React/Next.js frontend with a FastAPI backend, enabling role-based access control (RBAC) for the human-in-the-loop auditors.
