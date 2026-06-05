# Financial Operations Agent

A financial operations agent built from scratch using the Anthropic API and Python — no frameworks like LangChain or LangGraph.

## What it does
Given a customer ID, transaction amount, and destination country, the agent automatically checks:
- Whether the transaction is within the customer's limit
- Whether the destination country is compliant with financial regulations

It then returns a clear APPROVED or DENIED decision with reasoning.

## Why the architecture matters
The LLM never makes the final compliance decision — a deterministic Python rules engine does. This is critical in regulated financial environments where decisions must be auditable and consistent.

## How it works
1. User sends a natural language request
2. Claude reads the request and decides which tools to call
3. Python executes the tools — not Claude
4. Results are sent back to Claude
5. This loops until Claude has enough information to give a final answer

## Eval Results
- 10/10 test cases passed
- 100% accuracy across approved, denied, restricted country, and unknown customer scenarios

## How to run it

install dependencies
pip install anthropic python-dotenv

add your API key to .env
ANTHROPIC_API_KEY=your_key_here

run the agent
python agent.py

run the eval harness
python eval.py