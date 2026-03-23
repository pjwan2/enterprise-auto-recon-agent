# src/ai_agent/finops_agent.py

import os
import json
import time
import logging
from typing import TypedDict, Dict, Any
from pydantic import BaseModel, Field
import boto3
from botocore.exceptions import ClientError

# ==========================================
# 0. Enterprise Configuration & Logging
# ==========================================
from dotenv import load_dotenv
# Automatically load environment variables from the .env file
load_dotenv() 

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FinOpsAIAgent")

# LangGraph & Google AI components
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. Define the Structured Output & State
# ==========================================

class ResolutionPayload(BaseModel):
    root_cause_analysis: str = Field(description="A brief, professional explanation of why the transaction failed.")
    confidence_score: float = Field(description="Confidence in this resolution from 0.0 to 1.0.")
    proposed_fix_action: str = Field(description="Action to take. MUST BE one of: 'ISSUE_REFUND', 'UPDATE_LEDGER', 'MANUAL_INVESTIGATION'.")
    fix_payload: Dict[str, Any] = Field(description="The JSON data required to execute the fix. Must be valid JSON.")

class AgentState(TypedDict):
    receipt_handle: str  
    raw_message: dict    
    resolution: ResolutionPayload 
    status: str          

# ==========================================
# 2. Define the Agent Workflow (LangGraph)
# ==========================================

class FinOpsAgentOrchestrator:
    def __init__(self, dlq_name: str, region_name: str = "us-east-1"):
        self.dlq_name = dlq_name
        self._init_aws_client(region_name)
        self._init_llm_graph()

    def _init_aws_client(self, region_name):
        local_endpoint = os.getenv("LOCALSTACK_ENDPOINT")
        client_kwargs = {"region_name": region_name}
        
        if local_endpoint:
            client_kwargs.update({
                "endpoint_url": local_endpoint,
                "aws_access_key_id": "test",
                "aws_secret_access_key": "test"
            })
            
        self.sqs = boto3.client('sqs', **client_kwargs)
        
        try:
            self.dlq_url = self.sqs.get_queue_url(QueueName=self.dlq_name)['QueueUrl']
        except ClientError as e:
            logger.error(f"Failed to find SQS Queue '{self.dlq_name}'. Is LocalStack running?")
            raise e

    def _resolve_dynamic_model(self) -> str:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("🚨 GOOGLE_API_KEY is missing in .env file.")
            
        genai.configure(api_key=api_key)
        logger.info("📡 Querying Google AI API registry for active models...")
        
        valid_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name.lower():
                clean_name = m.name.replace("models/", "")
                valid_models.append(clean_name)
        
        if not valid_models:
            raise RuntimeError("No active Gemini models found.")
            
        pro_models = [m for m in valid_models if 'pro' in m and 'vision' not in m]
        flash_models = [m for m in valid_models if 'flash' in m and 'vision' not in m]
        
        selected_model = pro_models[0] if pro_models else (flash_models[0] if flash_models else valid_models[0])
        logger.info(f"✅ Dynamic Resolution Complete. Auto-selected Model: {selected_model}")
        return selected_model

    def _init_llm_graph(self):
        model_name = self._resolve_dynamic_model()
        
        try:
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        except ValueError:
            temperature = 0.0

        logger.info(f"🧠 Booting reasoning engine -> Model: {model_name} | Temp: {temperature}")
        
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        self.structured_llm = llm.with_structured_output(ResolutionPayload)

        workflow = StateGraph(AgentState)
        workflow.add_node("analyze_anomaly", self._node_analyze_anomaly)
        workflow.add_node("execute_resolution", self._node_execute_resolution)
        
        workflow.set_entry_point("analyze_anomaly")
        workflow.add_edge("analyze_anomaly", "execute_resolution")
        workflow.add_edge("execute_resolution", END)
        
        self.app = workflow.compile()

    def _node_analyze_anomaly(self, state: AgentState) -> AgentState:
        """Node 1: LLM analyzes the failure and generates a fix payload."""
        tx_id = state['raw_message']['transaction_data'].get('transaction_id', 'UNKNOWN')
        logger.info(f"🔍 Agent analyzing transaction: {tx_id}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Senior FinOps Data Analyst. Your job is to analyze failed payment transactions from a Dead Letter Queue and generate a deterministic JSON fix payload."),
            ("human", "Transaction Data: {data}\nFailure Reason: {reason}\nAnalyze the root cause and generate a fix.")
        ])
        
        chain = prompt | self.structured_llm
        
        try:
            resolution = chain.invoke({
                "data": json.dumps(state["raw_message"]["transaction_data"]),
                "reason": state["raw_message"]["failure_reason"]
            })
            state["resolution"] = resolution
        except Exception as e:
            logger.error(f"LLM Reasoning failed: {e}")
            state["status"] = "FAILED_REASONING"
            
        return state

    def _node_execute_resolution(self, state: AgentState) -> AgentState:
        """Node 2: Determines if the fix is safe to apply based on confidence."""
        res = state.get("resolution")
        if not res:
            return state

        if res.confidence_score >= 0.8 and res.proposed_fix_action != 'MANUAL_INVESTIGATION':
            logger.info(f"✅ AI Auto-Resolution Approved (Confidence: {res.confidence_score}). Action: {res.proposed_fix_action}")
            logger.info(f"📦 Fix Payload: {json.dumps(res.fix_payload)}")
            state["status"] = "RESOLVED"
            self._delete_from_dlq(state["receipt_handle"])
        else:
            logger.warning(f"⚠️ Escalating to HUMAN REVIEW. Action: {res.proposed_fix_action} | Confidence: {res.confidence_score}")
            
            # THE FIX: Route to a human review dashboard and break the poison pill loop!
            with open("human_review_dashboard.jsonl", "a") as f:
                escalation_record = {
                    "timestamp": time.time(),
                    "transaction_id": state['raw_message']['transaction_data'].get('transaction_id'),
                    "ai_analysis": res.model_dump() # Pydantic V2 safe
                }
                f.write(json.dumps(escalation_record) + "\n")
            
            logger.info("📁 Case routed to Human Dashboard. Purging from DLQ to prevent poison-pill loops.")
            state["status"] = "ESCALATED"
            self._delete_from_dlq(state["receipt_handle"])
            
        return state

    def _delete_from_dlq(self, receipt_handle: str):
        try:
            self.sqs.delete_message(QueueUrl=self.dlq_url, ReceiptHandle=receipt_handle)
            logger.info("🗑️ Message successfully purged from DLQ.")
        except ClientError as e:
            logger.error(f"Failed to delete message: {e}")

    def start_investigation_loop(self):
        logger.info("🤖 FinOps AI Agent is now polling the Dead Letter Queue...")
        while True:
            response = self.sqs.receive_message(
                QueueUrl=self.dlq_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5 
            )
            
            messages = response.get('Messages', [])
            if not messages:
                continue

            for msg in messages:
                raw_message = json.loads(msg['Body'])
                receipt_handle = msg['ReceiptHandle']
                
                initial_state = AgentState(
                    receipt_handle=receipt_handle,
                    raw_message=raw_message,
                    resolution=None,
                    status="PENDING"
                )
                
                self.app.invoke(initial_state)

if __name__ == "__main__":
    AGENT = FinOpsAgentOrchestrator(dlq_name="auto-recon-exceptions-dlq")
    AGENT.start_investigation_loop()