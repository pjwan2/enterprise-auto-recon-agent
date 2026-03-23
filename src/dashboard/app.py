# src/dashboard/app.py

import streamlit as st
import pandas as pd
import json
import os

# ==========================================
# 1. Enterprise Page Configuration
# ==========================================
st.set_page_config(
    page_title="FinOps Command Center",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for an enterprise dark-mode aesthetic
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .status-badge { padding: 5px 10px; border-radius: 15px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Data Loader (Simulating Database Fetch)
# ==========================================
DATA_FILE = "/app/human_review_dashboard.jsonl"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    
    records = []
    with open(DATA_FILE, "r") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

# ==========================================
# 3. UI Layout: Header & Metrics
# ==========================================
st.title("🏦 FinOps AI Command Center")
st.markdown("### Human-in-the-Loop (HITL) Exception Resolution Queue")

records = load_data()

# KPI Metrics Row
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Pending Manual Reviews", value=len(records), delta="Urgent" if len(records) > 5 else "Normal", delta_color="inverse")
with col2:
    st.metric(label="AI Auto-Resolved (24h)", value="1,245", delta="+12%")
with col3:
    st.metric(label="System Uptime", value="99.99%", delta="Stable")

st.divider()

# ==========================================
# 4. Interactive Review Workspace
# ==========================================
if not records:
    st.success("🎉 Inbox Zero! No pending anomalies requiring human review.")
else:
    # Sidebar List of Exceptions
    st.sidebar.header("🚨 Pending Escalations")
    selected_tx = None
    
    for i, record in enumerate(records):
        tx_id = record.get("transaction_id", f"UNKNOWN-{i}")
        if st.sidebar.button(f"TX: {tx_id[:8]}...", key=f"btn_{i}"):
            selected_tx = record

    # Main Detail View
    if selected_tx:
        st.subheader(f"🔍 Transaction Details: `{selected_tx.get('transaction_id')}`")
        
        # Split into two columns for comparison
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown("#### 🚨 Original Gateway Anomaly")
            st.error(selected_tx.get("original_issue", "Missing reason"))
            st.write("**Timestamp:**", pd.to_datetime(selected_tx.get("timestamp", 0), unit='s').strftime('%Y-%m-%d %H:%M:%S'))
            
        with detail_col2:
            st.markdown("#### 🤖 AI Root Cause Analysis")
            ai_data = selected_tx.get("ai_analysis", {})
            st.info(ai_data.get("root_cause_analysis", "AI could not determine the root cause."))
            
            confidence = ai_data.get("confidence_score", 0.0)
            st.progress(confidence, text=f"AI Confidence Score: {confidence * 100:.1f}%")

        st.markdown("#### 📦 Proposed Automated Fix (JSON Payload)")
        st.json(ai_data.get("fix_payload", {}))
        
        st.divider()
        
        # Action Buttons (Simulated execution)
        st.markdown("#### ⚡ Auditor Actions")
        btn_col1, btn_col2 = st.columns([1, 10])
        with btn_col1:
            if st.button("✅ Approve AI Fix", type="primary"):
                st.toast(f"Applying fix to ledger for {selected_tx.get('transaction_id')}...", icon="🚀")
                st.success("Ledger updated successfully. Transaction cleared.")
        with btn_col2:
            if st.button("❌ Reject & Escalate"):
                st.toast("Escalated to Level 2 Support.", icon="⚠️")
    else:
        st.info("👈 Select a transaction from the sidebar to begin investigation.")