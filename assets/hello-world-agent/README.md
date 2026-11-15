# Hello World Agent

A simple Hello World AI agent that greets users and responds to basic questions.

## Overview

Uses A2A Protocol, LangGraph, LiteLLM, and SAP Cloud SDK.

## Structure

- `app/main.py` - A2A server entry
- `app/agent_executor.py` - Request handling
- `app/agent.py` - Agent logic
- `app/prompt_injection_detector.py` - Tool result security scanning

## Local Run

Create a `.env` file:
```bash
export IBD_TESTING="1"

export AICORE_CLIENT_ID="sb-..."
export AICORE_CLIENT_SECRET='...'
export AICORE_AUTH_URL="https://...authentication...hana.ondemand.com"
export AICORE_BASE_URL="https://api...hana.ondemand.com"
```

Install dependencies and run:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt

source .env && python app/main.py
```

## Send a message

```bash
curl -s -X POST http://localhost:5000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0","id":"1","method":"message/send",
    "params":{"message":{
      "role":"user",
      "parts":[{"kind":"text","text":"Hello! What can you do?"}],
      "messageId":"msg-01",
      "kind":"message"
    }}
  }' | python3 -m json.tool
```

## Running Tests

```bash
source .env && pytest
```
