# Financial Operations Agent

A financial operations agent built from scratch using the Anthropic API and Python. No LangChain, no LangGraph — just the raw API and deliberate engineering decisions.

This project was built to demonstrate how agentic AI should be architected in regulated financial environments, not just how it can be assembled from tutorials.

## The Problem

Financial institutions spend $270 billion annually on compliance. The SEC imposed $8.2 billion in fines in 2024 alone, up 67% year over year. In H1 2025, financial crime fines surged 417%.

Production payments companies handle this with dedicated RegTech platforms, real-time OFAC feeds, and large engineering teams. This project isn't trying to replace that.

What it does show is the right set of architectural decisions for this problem: why the LLM should never make the final compliance call, why every decision needs an audit trail, why rules need to be updatable without redeploying code, and why eval harnesses matter before anything goes live.

The production version of this would swap SQLite for PostgreSQL, connect to a live OFAC sanctions API, add KYC/AML screening, and support multi-currency. The architecture here is designed to scale to all of that.

## The Core Design Decision

The LLM never makes the final compliance decision. A deterministic Python rules engine does.

This matters because LLMs hallucinate. You cannot let a model decide from memory whether Iran is sanctioned today. The Python rules engine makes that call every time, consistently and auditably. Claude's job is to understand the request and orchestrate the tools. Python's job is to execute the actual logic.

This is how production fintech AI systems are built.

## What's Inside

The agent accepts natural language requests, runs two compliance checks against a real database, logs every decision with a timestamp, and returns a clear APPROVED or DENIED with full reasoning.

There's a REST API with two endpoints — one for structured JSON input, one for natural language. A password-protected admin panel lets you add customers, update transaction limits, change country risk levels, and suspend accounts without touching any code. A separate eval harness runs 10 test cases automatically and scores accuracy.

Everything is deployed live on Railway.

## Tech Stack

Python 3.13, Anthropic API (Claude Haiku), FastAPI, SQLite, Railway

## How It Works

The user sends a natural language message. Claude decides which tools to call but does not execute them. Python runs the tools against the real database and returns results to Claude. Claude loops until it has enough information to make a final decision. Every decision is logged.

That loop is the entire agent. No magic, no hidden abstractions.

## Eval Results

10/10 test cases passed. 100% accuracy across approved transactions, limit violations, restricted countries, high-risk country thresholds, and unknown customer IDs.

## Live Demo

Main agent: https://web-production-af676.up.railway.app

Admin panel: https://web-production-af676.up.railway.app/admin
(username: admin, password: revanth2026)

API docs: https://web-production-af676.up.railway.app/docs

## API

Health check:
```
GET /health
```

Structured validation:
```bash
curl -X POST "https://web-production-af676.up.railway.app/transaction/validate" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "C-1042", "amount": 5000, "country": "Mexico"}'
```

Natural language:
```bash
curl -X POST "https://web-production-af676.up.railway.app/transaction/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to send $5,000 to Mexico. My customer ID is C-1042."}'
```

## Running Locally

```bash
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key_here" > .env
python database.py
uvicorn api:app --reload
```

To run the eval harness:
```bash
python eval.py
```

## Project Structure

```
financial-agent/
├── agent.py        # Tool definitions, implementations, and agent loop
├── api.py          # FastAPI wrapper
├── database.py     # SQLite setup and transaction logging
├── eval.py         # Evaluation harness
├── static/
│   ├── index.html  # Frontend UI
│   └── admin.html  # Admin panel
├── Procfile
└── requirements.txt
```

## Author

Revanth Kodati — [LinkedIn](https://linkedin.com/in/revanth-kodati) | [Portfolio](https://revanth-kodati-portfolio.vercel.app) | [Kaggle](https://kaggle.com/kodatirevanth)
