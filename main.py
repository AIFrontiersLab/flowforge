"""
Flowforge MVP - Workflow Orchestration Engine

Implements a simple webhook listener that processes payloads through
a simulated LLM classification node and routes to appropriate handlers.
"""
import os
import json
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Flowforge MVP")

# In-memory storage for demonstration
db_high_priority = []
db_logs = []

# Configuration
LLM_API_KEY = os.getenv("LLM_API_KEY", "fake_key_for_mvp")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "http://localhost:9999")

class WorkflowPayload(BaseModel):
    data: str
    metadata: Optional[Dict[str, Any]] = {}

class ExecutionResult(BaseModel):
    status: str
    workflow_id: str
    classification: str
    action_taken: str
    timestamp: float

def classify_text(text: str) -> str:
    """Simulate LLM classification based on keywords."""
    text_lower = text.lower()
    priority_keywords = ["urgent", "critical", "error", "fail", "down"]
    for keyword in priority_keywords:
        if keyword in text_lower:
            return "high_priority"
    return "standard"

def process_workflow(payload: WorkflowPayload) -> ExecutionResult:
    """Core workflow engine logic."""
    workflow_id = f"wf_{int(time.time())}_{hash(payload.data) % 10000}"
    
    # Step 1: LLM Classification
    classification = classify_text(payload.data)
    
    # Step 2: Conditional Routing
    action_taken = ""
    if classification == "high_priority":
        # Simulate external API call
        try:
            # In real MVP, this would use httpx
            # response = httpx.post(EXTERNAL_API_URL, json=payload.dict())
            action_taken = f"sent_to_external_api({EXTERNAL_API_URL})"
            db_high_priority.append({
                "id": workflow_id,
                "data": payload.data,
                "timestamp": time.time()
            })
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"External API failed: {str(e)}")
    else:
        # Log to local DB
        db_logs.append({
            "id": workflow_id,
            "data": payload.data,
            "timestamp": time.time()
        })
        action_taken = "logged_to_local_db"
    
    return ExecutionResult(
        status="completed",
        workflow_id=workflow_id,
        classification=classification,
        action_taken=action_taken,
        timestamp=time.time()
    )

@app.post("/webhook", response_model=ExecutionResult)
async def handle_webhook(payload: WorkflowPayload):
    """Webhook listener endpoint."""
    if not payload.data:
        raise HTTPException(status_code=400, detail="Data field is required")
    
    try:
        result = process_workflow(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Health check and stats."""
    return {
        "status": "running",
        "high_priority_count": len(db_high_priority),
        "log_count": len(db_logs)
    }

def demo():
    """Demonstrate core capability without running server."""
    test_payload = WorkflowPayload(data="Critical system failure detected")
    result = process_workflow(test_payload)
    print(json.dumps(result.dict(), indent=2))
    return result