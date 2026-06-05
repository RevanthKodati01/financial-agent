# Financial Operations Agent

A financial operations agent built from scratch using the Anthropic API and Python — no frameworks like LangChain or LangGraph. Built to demonstrate production-grade agentic AI engineering in a fintech context.

## The Problem

Financial institutions spend $270 billion annually on compliance. The SEC imposed $8.2 billion in fines in 2024 alone — a 67% increase year over year. In H1 2025, financial crime fines surged 417%.

Payments companies process thousands of cross-border transactions daily. Each one must be checked against customer limits and international compliance rules before execution. Manual review is slow and error-prone. A wrong approval in a sanctioned country is a regulatory violation.

This agent automates that decision — reliably, auditably, and at scale.

## Why the Architecture Matters

**The LLM never makes the final compliance decision — a deterministic Python rules engine does.**

This is the critical design choice. LLMs can hallucinate. In a regulated financial environment, you cannot let a model guess whether Iran is a sanctioned country. The Python rules engine makes that call every time — consistently, auditably, and without exception.

Claude's role: understand the request, orchestrate the tools, communicate the result.  
Python's role: execute the actual compliance and limit logic.

This maps directly to how production fintech AI systems are architected.

## Features

- Natural language transaction requests — no structured forms needed
- Two-tool agent loop — transaction limit check + compliance rules check
- Real SQLite database with customer and country data
- Full transaction audit trail with timestamps
- Conversation memory across multi-turn interactions
- Eval harness with 10 test cases — 100% accuracy
- REST API via FastAPI with two endpoints — structured and natural language
- Password-protected admin panel to manage customers and compliance rules dynamically
- Case-insensitive country matching
- Live deployment on Railway

## Why No Frameworks

No LangChain. No LangGraph. Pure Anthropic API and Python.

This means every line of code is explainable. Every architectural decision is deliberate. Frameworks hide complexity — this project exposes it so you can see exactly how agentic systems work under the hood.

## Tech Stack

- Python 3.13
- Anthropic API (Claude Haiku)
- FastAPI + Uvicorn
- SQLite
- Railway (deployment)

## How it Works

1. User sends a natural language request — *"I want to send $5,000 to Mexico. My customer ID is C-1042."*
2. Claude reads the request and decides which tools to call — it does NOT execute them
3. Python executes `check_transaction_limit` — queries the real database for the customer's limit
4. Python executes `check_compliance_rules` — checks the destination country against the rules engine
5. Results are sent back to Claude
6. This loop continues until Claude has enough information to give a final APPROVED or DENIED decision
7. Every decision is logged to the database with a timestamp

## Eval Results

```
Score: 10/10 passed
Accuracy: 100%
```

Test cases cover: approved transactions, limit exceeded, restricted countries (Iran, Cuba, Syria), high-risk countries (Russia, Venezuela), unknown customers, and boundary conditions.

## Live Demo

**Main Agent:** https://web-production-af676.up.railway.app

**Admin Panel:** https://web-production-af676.up.railway.app/admin  
Username: `admin` | Password: `jeeves2026`

**API Docs:** https://web-production-af676.up.railway.app/docs

## Live API

**Base URL:** `https://web-production-af676.up.railway.app`

**Health check:**
```
GET /health
```

**Structured transaction validation:**
```bash
curl -X POST "https://web-production-af676.up.railway.app/transaction/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "C-1042",
    "amount": 5000,
    "country": "Mexico"
  }'
```

**Natural language chat:**
```bash
curl -X POST "https://web-production-af676.up.railway.app/transaction/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to send $5,000 to Mexico. My customer ID is C-1042."}'
```

**Response:**
```json
{
  "decision": "APPROVED",
  "reason": "...",
  "customer_id": "C-1042",
  "amount": 5000.0,
  "country": "Mexico"
}
```

## How to Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Initialize the database
python database.py

# Run the interactive agent
python agent.py

# Run the eval harness
python eval.py

# Run the API server
uvicorn api:app --reload
```

## Project Structure

```
financial-agent/
├── agent.py          # Core agent — tool definitions, tool implementations, agent loop
├── api.py            # FastAPI wrapper — exposes agent as REST API
├── database.py       # SQLite setup, seeding, and transaction logging
├── eval.py           # Evaluation harness — 10 test cases, accuracy scoring
├── static/
│   ├── index.html    # Natural language frontend UI
│   └── admin.html    # Password-protected admin panel
├── Procfile          # Railway deployment config
├── requirements.txt  # Dependencies
└── .env              # API key (never committed)
```

## Author

Revanth Kodati — [LinkedIn](https://linkedin.com/in/revanth-kodati) | [Portfolio](https://revanth-kodati-portfolio.vercel.app) | [Kaggle](https://kaggle.com/kodatirevanth)
