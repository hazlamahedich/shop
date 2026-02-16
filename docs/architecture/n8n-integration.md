# n8n Integration Architecture

**Date:** 2026-02-15  
**Status:** Proposed  
**Related:** Integration Research, Natural Language Workflow Builder

---

## Overview

This document describes the integration of n8n workflow automation into the Shop app, enabling:

1. **Automated Workflows** - Trigger automations on app events (orders, messages)
2. **External Integrations** - Connect to 400+ services (Slack, email, CRMs)
3. **Merchant Customization** - Let merchants build their own automations
4. **Natural Language Builder** - Create workflows from plain English descriptions

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │   FastAPI        │  │      n8n         │  │      PostgreSQL          │  │
│  │   Backend        │◄─┤    :5678         │◄─┤     (shared DB)          │  │
│  │    :8000         │  │                  │  │                          │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────────┬─────────────┘  │
│           │                     │                         │                 │
│           │  REST API           │  Webhooks               │                 │
│           │  (create/trigger)   │  (callbacks)            │                 │
│           │                     │                         │                 │
│           │    ┌────────────────┴────────────────────────┐│                 │
│           │    │              n8n Workflows              ││                 │
│           │    │  ┌─────────┐  ┌─────────┐  ┌────────┐ ││                 │
│           │    │  │ Order   │  │ Message │  │ Custom │ ││                 │
│           │    │  │ Flow    │  │ Flow    │  │ Flow   │ ││                 │
│           │    │  └─────────┘  └─────────┘  └────────┘ ││                 │
│           │    └────────────────────────────────────────┘│                 │
│           │                                             │                 │
│  ┌────────┴─────────┐                                   │                 │
│  │      Redis       │                                   │                 │
│  │     (cache)      │                                   │                 │
│  └──────────────────┘                                   │                 │
│                                                         │                 │
│  ┌──────────────────────────────────────────────────────┴──────────────┐  │
│  │                        React Frontend                                │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │  │
│  │  │ WorkflowBuilder │  │ WorkflowList    │  │ n8n iframe embed    │  │  │
│  │  │ (NL → Workflow) │  │ (manage flows)  │  │ (visual editor)     │  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Components

### 1. Infrastructure Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| n8n Container | `docker.n8n.io/n8nio/n8n` | Workflow engine |
| PostgreSQL | Shared with app | n8n data persistence |
| Traefik | Reverse proxy | SSL, routing |

### 2. Backend Services

| Service | Location | Purpose |
|---------|----------|---------|
| `N8nClient` | `backend/app/services/n8n/client.py` | REST API client |
| `WorkflowGenerator` | `backend/app/services/n8n/workflow_generator.py` | NL → JSON conversion |
| `WebhookHandler` | `backend/app/api/webhooks/n8n.py` | Receive n8n callbacks |

### 3. Frontend Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `WorkflowBuilder` | `frontend/src/components/WorkflowBuilder.tsx` | NL workflow creation |
| `WorkflowList` | `frontend/src/components/WorkflowList.tsx` | Manage workflows |
| `N8nEmbed` | `frontend/src/components/N8nEmbed.tsx` | Visual editor iframe |

---

## Phase 1: Infrastructure Setup

### Docker Compose Configuration

```yaml
# docker-compose.yml (addition)
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=${N8N_HOST:-localhost}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://${N8N_HOST}/
      - GENERIC_TIMEZONE=UTC
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=${DB_USER}
      - DB_POSTGRESDB_PASSWORD=${DB_PASSWORD}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - N8N_USER_MANAGEMENT_JWT_SECRET=${JWT_SECRET}
      - N8N_PUBLIC_API_DISABLED=false
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.n8n.rule=Host(`n8n.${DOMAIN}`)"

volumes:
  n8n_data:
```

### Database Setup

```sql
-- Create n8n database in PostgreSQL
CREATE DATABASE n8n;
```

---

## Phase 2: Backend Integration

### Directory Structure

```
backend/app/
├── services/
│   ├── n8n/
│   │   ├── __init__.py
│   │   ├── client.py              # N8nClient - REST API wrapper
│   │   ├── workflow_generator.py  # NL → JSON conversion
│   │   ├── node_catalog.py        # Available n8n nodes for LLM
│   │   └── prompts.py             # System prompts for LLM
│   └── ...
├── api/
│   ├── webhooks/
│   │   ├── n8n.py                 # Receive callbacks from n8n
│   │   └── ...
│   └── workflows/
│       ├── __init__.py
│       └── routes.py              # Workflow CRUD endpoints
└── core/
    └── config.py                  # Add N8N_URL, N8N_API_KEY
```

### N8nClient Service

```python
# backend/app/services/n8n/client.py
"""n8n REST API client for workflow management."""

import httpx
from typing import Optional
from app.core.config import settings

class N8nClient:
    """Client for interacting with n8n REST API."""
    
    def __init__(self):
        self.base_url = settings.N8N_URL
        self.api_key = settings.N8N_API_KEY
        self.headers = {"X-N8N-API-KEY": self.api_key}
    
    async def _request(
        self, 
        method: str, 
        path: str, 
        json: Optional[dict] = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}/api/v1{path}",
                headers=self.headers,
                json=json
            )
            response.raise_for_status()
            return response.json()
    
    # Workflow Management
    async def list_workflows(self, tags: Optional[str] = None) -> list:
        params = {"tags": tags} if tags else {}
        return await self._request("GET", "/workflows", params)
    
    async def get_workflow(self, workflow_id: str) -> dict:
        return await self._request("GET", f"/workflows/{workflow_id}")
    
    async def create_workflow(
        self, 
        workflow: dict, 
        activate: bool = False
    ) -> dict:
        result = await self._request("POST", "/workflows", json=workflow)
        if activate and result.get("id"):
            await self.activate_workflow(result["id"])
            result["active"] = True
        return result
    
    async def update_workflow(self, workflow_id: str, workflow: dict) -> dict:
        return await self._request("PUT", f"/workflows/{workflow_id}", json=workflow)
    
    async def delete_workflow(self, workflow_id: str) -> dict:
        return await self._request("DELETE", f"/workflows/{workflow_id}")
    
    async def activate_workflow(self, workflow_id: str) -> dict:
        return await self._request("POST", f"/workflows/{workflow_id}/activate")
    
    async def deactivate_workflow(self, workflow_id: str) -> dict:
        return await self._request("POST", f"/workflows/{workflow_id}/deactivate")
    
    # Webhook Trigger
    async def trigger_webhook(
        self, 
        webhook_path: str, 
        data: dict
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/webhook/{webhook_path}",
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    # Credentials
    async def create_credential(self, credential: dict) -> dict:
        return await self._request("POST", "/credentials", json=credential)
    
    async def list_credentials(self) -> list:
        return await self._request("GET", "/credentials")
    
    # Executions
    async def list_executions(
        self, 
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> list:
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        if status:
            params["status"] = status
        return await self._request("GET", "/executions", params)
    
    async def retry_execution(self, execution_id: str) -> dict:
        return await self._request("POST", f"/executions/{execution_id}/retry")


# Singleton instance
n8n_client = N8nClient()
```

### Webhook Callbacks

```python
# backend/app/api/webhooks/n8n.py
"""Receive callbacks from n8n workflows."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.core.auth import verify_webhook_signature
from app.services.orders import OrderService
from app.services.messaging import MessagingService

router = APIRouter(prefix="/webhooks/n8n", tags=["n8n-callbacks"])


class N8nCallbackPayload(BaseModel):
    workflow_id: str
    execution_id: str
    event: str
    data: dict
    merchant_id: str


@router.post("/callback")
async def n8n_callback(
    payload: N8nCallbackPayload,
    background_tasks: BackgroundTasks,
    verified: bool = Depends(verify_webhook_signature)
):
    """
    Receive callbacks from n8n workflows.
    
    Used for:
    - Workflow completion notifications
    - Error handling
    - Data sync back to app
    """
    if not verified:
        raise HTTPException(403, "Invalid webhook signature")
    
    # Route based on event type
    match payload.event:
        case "order.notification.sent":
            # Update order status in DB
            background_tasks.add_task(
                OrderService.mark_notified,
                payload.data.get("order_id")
            )
        
        case "customer.synced":
            # Update customer record
            pass
        
        case "workflow.error":
            # Log error, alert merchant
            pass
    
    return {"received": True}
```

---

## Phase 3: Natural Language Workflow Builder

### Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Natural Language → n8n Workflow                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User: "When a new order comes in, send a Slack notification       │
│         to the #orders channel and add the customer to Mailchimp"  │
│                                                                     │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 Your LLM (Ollama/OpenAI/etc)                 │   │
│  │  + n8n node catalog + workflow JSON schema                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Generated Workflow JSON                    │   │
│  │  {                                                           │   │
│  │    "name": "Order → Slack + Mailchimp",                      │   │
│  │    "nodes": [                                                │   │
│  │      { "type": "n8n-nodes-base.webhook", ... },              │   │
│  │      { "type": "n8n-nodes-base.slack", ... },                │   │
│  │      { "type": "n8n-nodes-base.mailchimp", ... }             │   │
│  │    ],                                                        │   │
│  │    "connections": { ... }                                    │   │
│  │  }                                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  POST /api/v1/workflows                       │   │
│  │                         → n8n                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ▼                                      │
│                    ✅ Workflow created & activated                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Node Catalog

```python
# backend/app/services/n8n/node_catalog.py
"""Catalog of n8n nodes for LLM context."""

N8N_node_CATALOG = """
## Available n8n Nodes

### Trigger Nodes (start workflow)
- n8n-nodes-base.webhook: Receive HTTP requests
  - Parameters: httpMethod (GET/POST), path (string), authentication (none/headerAuth)
- n8n-nodes-base.schedule: Run on schedule
  - Parameters: rule (cron expression), timezone
- n8n-nodes-base.manualTrigger: Manual execution (testing)
- n8n-nodes-base.emailTrigger: Trigger on incoming email

### App-Specific Triggers (your app)
- webhook.shopify.order: Trigger when Shopify order created
  - Output: { order_id, customer_email, total, items }
- webhook.facebook.message: Trigger when FB message received
  - Output: { sender_id, message, timestamp }
- webhook.app.custom: Trigger on custom app events
  - Output: { event_type, data }

### Communication Nodes
- n8n-nodes-base.slack: Send Slack messages
  - Parameters: channel (string), text (string)
- n8n-nodes-base.emailSend: Send emails via SMTP
  - Parameters: fromEmail, toEmail, subject, text
- n8n-nodes-base.gmail: Send via Gmail
  - Parameters: to, subject, message

### Marketing Nodes
- n8n-nodes-base.mailchimp: Mailchimp operations
  - Operations: addMember, updateMember, getMember
- n8n-nodes-base.hubspot: HubSpot CRM
  - Operations: createContact, updateContact

### Data Nodes
- n8n-nodes-base.googleSheets: Google Sheets operations
- n8n-nodes-base.airtable: Airtable operations
- n8n-nodes-base.httpRequest: HTTP requests to any API
  - Parameters: url, method, authentication, headers, body

### Logic Nodes
- n8n-nodes-base.if: Conditional branching
  - Parameters: conditions (array of {value1, operation, value2})
- n8n-nodes-base.switch: Multiple conditions
- n8n-nodes-base.merge: Combine data from multiple inputs
- n8n-nodes-base.code: Run custom JavaScript/Python
  - Parameters: language (javaScript/python), code (string)
- n8n-nodes-base.set: Transform/set data values
  - Parameters: values (object with key-value pairs)

### Utility Nodes
- n8n-nodes-base.wait: Pause execution
  - Parameters: amount (number), unit (seconds/minutes/hours/days)
- n8n-nodes-base.errorTrigger: Handle workflow errors
"""
```

### LLM System Prompt

```python
# backend/app/services/n8n/prompts.py
"""System prompts for workflow generation."""

WORKFLOW_GENERATION_SYSTEM_PROMPT = """
You are an n8n workflow generator. Convert natural language instructions into valid n8n workflow JSON.

## Output Schema
```json
{
  "name": "Workflow name",
  "nodes": [
    {
      "id": "unique-id",
      "name": "Display Name",
      "type": "n8n-nodes-base.<nodeType>",
      "typeVersion": 1,
      "position": [x, y],
      "parameters": { ... node-specific params ... }
    }
  ],
  "connections": {
    "Source Node Name": {
      "main": [[{ "node": "Target Node Name", "type": "main", "index": 0 }]]
    }
  },
  "settings": {
    "saveExecutionProgress": true,
    "saveManualExecutions": true
  }
}
```

## Rules
1. Every workflow needs a trigger node (webhook, schedule, or manual)
2. Position nodes with 200px spacing horizontally (start at [250, 300])
3. Use descriptive node names
4. Include all required parameters for each node type
5. For expressions, use n8n syntax: ={{$json.fieldName}}
6. Output ONLY valid JSON, no markdown code blocks or explanation

## Common Patterns

### Pattern: Event → Action
```
User: "When X happens, do Y"
→ Trigger node for X → Action node for Y
```

### Pattern: Event → Condition → Multiple Actions
```
User: "When X happens, if condition, do Y and Z"
→ Trigger → IF node → Action Y (true branch), Action Z (true branch)
```

### Pattern: Scheduled Task
```
User: "Every day at 9am, do X"
→ Schedule trigger (cron: "0 9 * * *") → Action X
```

## Example

Input: "Send a Slack message when a webhook is called with the message from the request body"

Output:
{
  "name": "Webhook to Slack",
  "nodes": [
    {
      "id": "webhook-1",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "notify",
        "authentication": "none"
      }
    },
    {
      "id": "slack-1",
      "name": "Send to Slack",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [450, 300],
      "parameters": {
        "channel": "#general",
        "text": "={{$json.body.message}}"
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "Send to Slack", "type": "main", "index": 0}]]
    }
  },
  "settings": {
    "saveExecutionProgress": true,
    "saveManualExecutions": true
  }
}
"""
```

### Workflow Generator Service

```python
# backend/app/services/n8n/workflow_generator.py
"""Generate n8n workflows from natural language."""

import json
import re
from typing import Optional
from app.services.llm.base import LLMProvider
from app.services.n8n.client import n8n_client
from app.services.n8n.prompts import WORKFLOW_GENERATION_SYSTEM_PROMPT
from app.services.n8n.node_catalog import N8N_NODE_CATALOG


class WorkflowGeneratorError(Exception):
    """Raised when workflow generation fails."""
    pass


class WorkflowGenerator:
    """Generate n8n workflows from natural language instructions."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm
    
    async def generate_from_nl(
        self,
        instruction: str,
        merchant_id: str,
        activate: bool = False,
        custom_nodes: Optional[str] = None
    ) -> dict:
        """
        Generate n8n workflow from natural language.
        
        Args:
            instruction: Natural language workflow description
            merchant_id: Merchant ID for tagging/isolation
            activate: Whether to activate after creation
            custom_nodes: Additional custom node documentation
        
        Returns:
            Created workflow object from n8n API
        """
        # Build prompt with context
        prompt = self._build_prompt(instruction, custom_nodes)
        
        # Call LLM
        response = await self.llm.generate(
            prompt,
            system_prompt=WORKFLOW_GENERATION_SYSTEM_PROMPT
        )
        
        # Parse JSON from response
        try:
            workflow = self._parse_json(response)
        except json.JSONDecodeError as e:
            raise WorkflowGeneratorError(
                f"Failed to parse LLM response as JSON: {e}"
            )
        
        # Validate and fix structure
        workflow = self._validate_and_fix(workflow)
        
        # Add merchant tag for multi-tenancy
        workflow["tags"] = [{"name": f"merchant:{merchant_id}"}]
        
        # Create via n8n API
        created = await n8n_client.create_workflow(workflow, activate=activate)
        
        return created
    
    def _build_prompt(
        self, 
        instruction: str, 
        custom_nodes: Optional[str] = None
    ) -> str:
        """Build the full prompt for the LLM."""
        parts = [
            "## Available Nodes",
            N8N_NODE_CATALOG,
        ]
        
        if custom_nodes:
            parts.append("\n### Custom App Nodes")
            parts.append(custom_nodes)
        
        parts.extend([
            "\n## User Instruction",
            instruction,
            "\n## Generated Workflow JSON",
        ])
        
        return "\n".join(parts)
    
    def _parse_json(self, text: str) -> dict:
        """Extract and parse JSON from LLM response."""
        # Remove markdown code blocks if present
        text = text.strip()
        
        if "```json" in text:
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        elif "```" in text:
            match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        
        return json.loads(text)
    
    def _validate_and_fix(self, workflow: dict) -> dict:
        """Validate workflow structure and fix common issues."""
        # Ensure required top-level fields
        workflow.setdefault("name", "Generated Workflow")
        workflow.setdefault("nodes", [])
        workflow.setdefault("connections", {})
        workflow.setdefault("settings", {
            "saveExecutionProgress": True,
            "saveManualExecutions": True
        })
        
        # Validate nodes
        trigger_types = {
            "n8n-nodes-base.webhook",
            "n8n-nodes-base.schedule",
            "n8n-nodes-base.manualTrigger",
            "n8n-nodes-base.emailTrigger",
        }
        
        has_trigger = any(
            node.get("type") in trigger_types 
            for node in workflow["nodes"]
        )
        
        if not has_trigger:
            # Add manual trigger as fallback
            workflow["nodes"].insert(0, {
                "id": "manual-trigger",
                "name": "Manual Trigger",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {}
            })
        
        # Ensure unique IDs and positions
        for i, node in enumerate(workflow["nodes"]):
            node.setdefault("id", f"node-{i}")
            node.setdefault("typeVersion", 1)
            if "position" not in node:
                node["position"] = [250 + (i * 200), 300]
        
        return workflow
    
    async def suggest_improvements(
        self, 
        workflow_id: str
    ) -> list[str]:
        """Analyze a workflow and suggest improvements."""
        workflow = await n8n_client.get_workflow(workflow_id)
        
        prompt = f"""
Analyze this n8n workflow and suggest improvements:

{json.dumps(workflow, indent=2)}

Provide 3-5 specific, actionable suggestions for:
- Error handling
- Performance
- Maintainability
- Best practices

Output as a JSON array of strings.
"""
        
        response = await self.llm.generate(prompt)
        return self._parse_json(response)


# Factory function
def get_workflow_generator() -> WorkflowGenerator:
    """Get configured workflow generator instance."""
    from app.services.llm import get_llm_provider
    return WorkflowGenerator(llm=get_llm_provider())
```

### API Endpoints

```python
# backend/app/api/workflows/routes.py
"""Workflow management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.n8n.client import n8n_client
from app.services.n8n.workflow_generator import get_workflow_generator
from app.core.auth import get_current_merchant

router = APIRouter(prefix="/workflows", tags=["workflows"])


class GenerateWorkflowRequest(BaseModel):
    instruction: str = Field(..., min_length=10, max_length=2000)
    activate: bool = False


class GenerateWorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    active: bool
    node_count: int
    preview_url: str
    edit_url: str


class WorkflowSummary(BaseModel):
    id: str
    name: str
    active: bool
    created_at: str
    updated_at: str
    tags: list


@router.post("/generate", response_model=GenerateWorkflowResponse)
async def generate_workflow(
    req: GenerateWorkflowRequest,
    merchant = Depends(get_current_merchant)
):
    """
    Generate n8n workflow from natural language instruction.
    
    Uses the configured LLM to convert plain English into a valid
    n8n workflow JSON, then creates it via the n8n API.
    """
    generator = get_workflow_generator()
    
    try:
        workflow = await generator.generate_from_nl(
            instruction=req.instruction,
            merchant_id=merchant.id,
            activate=req.activate
        )
    except Exception as e:
        raise HTTPException(400, f"Workflow generation failed: {str(e)}")
    
    return GenerateWorkflowResponse(
        workflow_id=workflow["id"],
        name=workflow["name"],
        active=workflow.get("active", False),
        node_count=len(workflow.get("nodes", [])),
        preview_url=f"{settings.N8N_URL}/workflow/{workflow['id']}",
        edit_url=f"{settings.N8N_URL}/workflow/{workflow['id']}"
    )


@router.get("", response_model=list[WorkflowSummary])
async def list_workflows(
    merchant = Depends(get_current_merchant)
):
    """List all workflows for the current merchant."""
    workflows = await n8n_client.list_workflows(
        tags=f"merchant:{merchant.id}"
    )
    
    return [
        WorkflowSummary(
            id=w["id"],
            name=w["name"],
            active=w.get("active", False),
            created_at=w.get("createdAt", ""),
            updated_at=w.get("updatedAt", ""),
            tags=w.get("tags", [])
        )
        for w in workflows
    ]


@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    merchant = Depends(get_current_merchant)
):
    """Activate a workflow."""
    result = await n8n_client.activate_workflow(workflow_id)
    return {"status": "activated", "workflow_id": workflow_id}


@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    merchant = Depends(get_current_merchant)
):
    """Deactivate a workflow."""
    result = await n8n_client.deactivate_workflow(workflow_id)
    return {"status": "deactivated", "workflow_id": workflow_id}


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    merchant = Depends(get_current_merchant)
):
    """Delete a workflow."""
    await n8n_client.delete_workflow(workflow_id)
    return {"status": "deleted", "workflow_id": workflow_id}


@router.post("/{workflow_id}/trigger")
async def trigger_workflow(
    workflow_id: str,
    data: dict,
    merchant = Depends(get_current_merchant)
):
    """Manually trigger a workflow via webhook."""
    # Get workflow to find webhook path
    workflow = await n8n_client.get_workflow(workflow_id)
    
    # Find webhook node
    webhook_node = next(
        (n for n in workflow.get("nodes", []) 
         if n.get("type") == "n8n-nodes-base.webhook"),
        None
    )
    
    if not webhook_node:
        raise HTTPException(400, "Workflow has no webhook trigger")
    
    webhook_path = webhook_node.get("parameters", {}).get("path", "")
    
    result = await n8n_client.trigger_webhook(webhook_path, data)
    return {"status": "triggered", "result": result}
```

---

## Phase 4: Frontend Integration

### Workflow Builder Component

```tsx
// frontend/src/components/WorkflowBuilder.tsx
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';

interface WorkflowBuilderProps {
  onSuccess?: (workflowId: string) => void;
}

export function WorkflowBuilder({ onSuccess }: WorkflowBuilderProps) {
  const [instruction, setInstruction] = useState('');
  const [activate, setActivate] = useState(false);
  
  const generateMutation = useMutation({
    mutationFn: (data: { instruction: string; activate: boolean }) =>
      api.post('/workflows/generate', data),
    onSuccess: (data) => {
      onSuccess?.(data.workflow_id);
    }
  });

  const suggestions = [
    "When a new order is placed, send me an email with the order details",
    "Post to Slack when a customer abandons their cart",
    "Add new customers to my Mailchimp list automatically",
    "Send a follow-up message 24 hours after purchase",
    "Sync orders to a Google Sheet daily",
  ];

  const handleSubmit = () => {
    if (instruction.trim()) {
      generateMutation.mutate({ instruction, activate });
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-2">Create Automation</h2>
      <p className="text-gray-600 mb-6">
        Describe what you want to automate in plain English
      </p>
      
      <textarea
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        placeholder="e.g., When a customer places an order, send a Slack message to #orders and add them to Mailchimp"
        className="w-full h-32 p-4 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500"
      />
      
      <div className="flex items-center mt-4 mb-4">
        <input
          type="checkbox"
          id="activate"
          checked={activate}
          onChange={(e) => setActivate(e.target.checked)}
          className="mr-2"
        />
        <label htmlFor="activate" className="text-sm text-gray-700">
          Activate immediately after creation
        </label>
      </div>
      
      <button
        onClick={handleSubmit}
        disabled={!instruction.trim() || generateMutation.isPending}
        className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium 
                   disabled:bg-gray-300 disabled:cursor-not-allowed
                   hover:bg-blue-700 transition-colors"
      >
        {generateMutation.isPending ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Generating...
          </span>
        ) : 'Create Workflow'}
      </button>
      
      <div className="mt-6">
        <p className="text-sm text-gray-500 mb-3">Try these examples:</p>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => setInstruction(s)}
              className="px-3 py-2 bg-gray-100 rounded-lg text-sm text-left
                       hover:bg-gray-200 transition-colors max-w-full truncate"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      
      {generateMutation.isSuccess && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-medium text-green-800">Workflow created!</span>
          </div>
          <div className="mt-3 flex gap-3">
            <a
              href={generateMutation.data.edit_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline text-sm"
            >
              Open in editor →
            </a>
          </div>
        </div>
      )}
      
      {generateMutation.isError && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <span className="text-red-800">
            Failed to generate workflow. Please try a different description.
          </span>
        </div>
      )}
    </div>
  );
}
```

### Workflow List Component

```tsx
// frontend/src/components/WorkflowList.tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

export function WorkflowList() {
  const queryClient = useQueryClient();
  
  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => api.get('/workflows'),
  });
  
  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.post(`/workflows/${id}/${active ? 'deactivate' : 'activate'}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  });
  
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/workflows/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  });

  if (isLoading) {
    return <div className="p-6">Loading workflows...</div>;
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Your Automations</h2>
      
      {!workflows?.length ? (
        <p className="text-gray-600">No workflows yet. Create one to get started!</p>
      ) : (
        <div className="space-y-4">
          {workflows.map((wf: any) => (
            <div
              key={wf.id}
              className="flex items-center justify-between p-4 border rounded-lg"
            >
              <div>
                <h3 className="font-medium">{wf.name}</h3>
                <p className="text-sm text-gray-500">
                  {wf.active ? 'Active' : 'Inactive'}
                </p>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => toggleMutation.mutate({ 
                    id: wf.id, 
                    active: wf.active 
                  })}
                  className={`px-4 py-2 rounded-lg ${
                    wf.active 
                      ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                      : 'bg-green-100 text-green-800 hover:bg-green-200'
                  }`}
                >
                  {wf.active ? 'Deactivate' : 'Activate'}
                </button>
                
                <a
                  href={`${import.meta.env.VITE_N8N_URL}/workflow/${wf.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200"
                >
                  Edit
                </a>
                
                <button
                  onClick={() => {
                    if (confirm('Delete this workflow?')) {
                      deleteMutation.mutate(wf.id);
                    }
                  }}
                  className="px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Multi-Tenancy Strategy

### Tenant Isolation

| Aspect | Implementation |
|--------|----------------|
| **Workflows** | Tag each workflow with `merchant:{id}` |
| **Credentials** | Store per-merchant, scoped access |
| **Webhooks** | Include `merchant_id` in all payloads |
| **UI Access** | SSO with JWT → n8n user management |
| **API Filtering** | Query workflows by merchant tag |

### Webhook Payload Structure

```json
{
  "merchant_id": "123",
  "event_type": "order.created",
  "timestamp": "2026-02-15T10:00:00Z",
  "data": {
    "order_id": "ORD-456",
    "customer_email": "customer@example.com",
    "total": 99.99,
    "items": [...]
  },
  "signature": "hmac-sha256-hash"
}
```

---

## Security Considerations

### 1. API Key Authentication

All n8n API calls require the `X-N8N-API-KEY` header.

```bash
# Generate API key in n8n UI
Settings → n8n API → Create API Key
```

### 2. Webhook Signature Verification

```python
import hmac
import hashlib

def verify_n8n_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 3. SSO Integration

n8n supports JWT-based authentication that can integrate with your existing auth:

```yaml
# n8n environment variables
N8N_USER_MANAGEMENT_JWT_SECRET: ${JWT_SECRET}
N8N_JWT_AUTH_HEADER: Authorization
```

### 4. Network Security

- n8n should not be exposed directly to the internet
- Use Traefik/nginx reverse proxy with authentication
- Restrict webhook access to known IPs if possible

---

## Configuration

### Environment Variables

```bash
# .env additions
N8N_URL=https://n8n.yourdomain.com
N8N_API_KEY=n8n-api-key-here
N8N_ENCRYPTION_KEY=32-character-encryption-key
N8N_WEBHOOK_SECRET=webhook-signing-secret
```

### Config Updates

```python
# backend/app/core/config.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # n8n Integration
    N8N_URL: str = "http://localhost:5678"
    N8N_API_KEY: str
    N8N_ENCRYPTION_KEY: str
    N8N_WEBHOOK_SECRET: str
```

---

## Example Workflows

### Example 1: Order Notification

```json
{
  "name": "Order → Slack Notification",
  "nodes": [
    {
      "id": "webhook-1",
      "name": "Order Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "order-created",
        "authentication": "headerAuth"
      }
    },
    {
      "id": "slack-1",
      "name": "Notify Slack",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 1,
      "position": [450, 300],
      "parameters": {
        "channel": "#orders",
        "text": "=🛒 New Order: {{$json.body.order_id}}\nCustomer: {{$json.body.customer_email}}\nTotal: ${{$json.body.total}}"
      }
    }
  ],
  "connections": {
    "Order Webhook": {
      "main": [[{"node": "Notify Slack", "type": "main", "index": 0}]]
    }
  }
}
```

### Example 2: Abandoned Cart Reminder

```json
{
  "name": "Abandoned Cart → Email Reminder",
  "nodes": [
    {
      "id": "webhook-1",
      "name": "Cart Abandoned",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "cart-abandoned"
      }
    },
    {
      "id": "wait-1",
      "name": "Wait 2 Hours",
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1,
      "position": [450, 300],
      "parameters": {
        "amount": 2,
        "unit": "hours"
      }
    },
    {
      "id": "http-1",
      "name": "Check Cart Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 1,
      "position": [650, 300],
      "parameters": {
        "url": "={{$env.APP_URL}}/api/carts/{{$json.body.cart_id}}",
        "method": "GET"
      }
    },
    {
      "id": "if-1",
      "name": "Still Abandoned?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [850, 300],
      "parameters": {
        "conditions": {
          "string": [
            {"value1": "={{$json.status}}", "value2": "abandoned"}
          ]
        }
      }
    },
    {
      "id": "email-1",
      "name": "Send Reminder",
      "type": "n8n-nodes-base.emailSend",
      "typeVersion": 1,
      "position": [1050, 200],
      "parameters": {
        "fromEmail": "noreply@shop.com",
        "toEmail": "={{$json.customer_email}}",
        "subject": "You left something in your cart!",
        "text": "Complete your purchase..."
      }
    }
  ],
  "connections": {
    "Cart Abandoned": {"main": [[{"node": "Wait 2 Hours", "type": "main", "index": 0}]]},
    "Wait 2 Hours": {"main": [[{"node": "Check Cart Status", "type": "main", "index": 0}]]},
    "Check Cart Status": {"main": [[{"node": "Still Abandoned?", "type": "main", "index": 0}]]},
    "Still Abandoned?": {"main": [[{"node": "Send Reminder", "type": "main", "index": 0}], []]}
  }
}
```

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_n8n_client.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.n8n.client import N8nClient

@pytest.fixture
def n8n_client():
    return N8nClient()

@pytest.mark.asyncio
async def test_create_workflow(n8n_client):
    with patch.object(n8n_client, '_request', new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "123", "name": "Test"}
        
        result = await n8n_client.create_workflow({"name": "Test"})
        
        assert result["id"] == "123"
        mock.assert_called_once_with("POST", "/workflows", json={"name": "Test"})


# backend/tests/test_workflow_generator.py
import pytest
from app.services.n8n.workflow_generator import WorkflowGenerator

@pytest.fixture
def generator():
    return WorkflowGenerator(llm=MockLLM())

def test_validate_and_fix_adds_trigger(generator):
    workflow = {
        "name": "Test",
        "nodes": [{"id": "1", "type": "n8n-nodes-base.slack"}]
    }
    
    fixed = generator._validate_and_fix(workflow)
    
    assert any(
        n["type"] == "n8n-nodes-base.manualTrigger" 
        for n in fixed["nodes"]
    )
```

### Integration Tests

```python
# backend/tests/integration/test_n8n_integration.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_generate_workflow_endpoint(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/workflows/generate",
        json={
            "instruction": "Send an email when a webhook is called",
            "activate": False
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "workflow_id" in data
    assert "preview_url" in data
```

---

## Implementation Timeline

| Phase | Tasks | Effort | Priority |
|-------|-------|--------|----------|
| **Phase 1** | Docker setup, DB config, environment | 2-3 hours | P0 |
| **Phase 2** | N8nClient, webhook callbacks | 4-6 hours | P0 |
| **Phase 3** | Workflow generator, NL builder | 6-8 hours | P1 |
| **Phase 4** | Frontend components | 4-6 hours | P1 |
| **Phase 5** | Multi-tenancy, templates | 4-6 hours | P2 |
| **Phase 6** | Testing, documentation | 3-4 hours | P1 |
| **Total** | | **23-33 hours** | |

---

## Related Documents

- [E-Commerce Abstraction Layer](/docs/architecture/ecommerce-abstraction.md)
- [LLM Abstraction Patterns](/docs/epic-1-llm-abstraction-patterns.md)
- [Security Patterns](/docs/epic-1-security-patterns.md)
- [Project Context](/docs/project-context.md)

---

## External References

- [n8n Documentation](https://docs.n8n.io)
- [n8n API Reference](https://docs.n8n.io/api/)
- [n8n Self-Hosting Guide](https://docs.n8n.io/hosting/installation/docker/)
- [MCP n8n Builder](https://github.com/spences10/mcp-n8n-builder)
