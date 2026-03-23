# 🏦 Enterprise AI-Driven FinOps Reconciliation Engine

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python)
![AWS](https://img.shields.io/badge/AWS-LocalStack-FF9900?style=for-the-badge&logo=amazonaws)
![LangChain](https://img.shields.io/badge/LangGraph-Agentic_AI-1C3C3C?style=for-the-badge)
![Pydantic](https://img.shields.io/badge/Pydantic-V2-E92063?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)

> An event-driven, resilient microservices architecture simulating high-frequency trading reconciliation. It features a fully autonomous **LangGraph Multi-Agent system** that investigates ledger anomalies, resolves edge cases via LLMs, and safely manages message queue lifecycles.

---

## 🏗️ System Architecture
<img width="906" height="662" alt="image" src="https://github.com/user-attachments/assets/f3469511-dac6-40a8-8dfc-f7e207bd5921" />


The system is designed with a strict **Event-Driven Architecture (EDA)**, mimicking the infrastructure of top-tier Fintech companies.

1. **High-Frequency Producer:** Streams simulated financial transactions into AWS Kinesis with strict partition key hashing (`user_id`) to guarantee temporal ordering.
2. **Real-Time Consumer:** A stream processor that performs real-time ledger vs. gateway reconciliation. Healthy records are cleared; anomalies (e.g., currency slippage, missing gateways) are securely routed to an SQS Dead Letter Queue (DLQ).
3. **Agentic FinOps Orchestrator:** A LangGraph-powered state machine that polls the DLQ, dynamically discovers the optimal LLM, performs root-cause analysis, and generates deterministic JSON fix payloads.

---

## 🔥 Engineering Highlights

This project is built to demonstrate resilience, determinism, and FinOps awareness:

* 🛡️ **Poison Pill Loop Prevention:** Engineered a graceful degradation mechanism. If the AI confidence is low (<0.8) or requires human intervention, the payload is safely escalated to a `Human Review Dashboard` and explicitly purged from the DLQ, completely eliminating infinite retry loops and runaway LLM API costs.
* 📡 **Dynamic Capability Discovery:** To prevent system outages caused by deprecated model endpoints (e.g., 404 Not Found), the Agent utilizes Google Generative AI's `ListModels` registry to dynamically resolve and bind to the most capable, active model at runtime.
* 🧱 **API-Level Determinism:** Eradicated LLM hallucinations by enforcing strict structured outputs. Utilizing `Pydantic V2` schemas and native API Function Calling, the Agent is constrained to output 100% executable JSON patch payloads.
* 💰 **Zero-Cost FinOps Sandboxing:** Fully decoupled from production AWS billing. The entire infrastructure (Kinesis, SQS) is orchestrated locally via `LocalStack` and `Docker Compose`, providing a completely isolated and free development environment.

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
* Docker & Docker Compose
* Python 3.11+
* A Google Gemini API Key

### 2. Environment Configuration
Create a `.env` file in the root directory (this is ignored by Git):
```env
LOCALSTACK_ENDPOINT=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1

GOOGLE_API_KEY=your_gemini_api_key_here
