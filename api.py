import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import anthropic
from agent import run_agent, check_transaction_limit, check_compliance_rules, tools, system_prompt
from database import initialize_database, log_transaction, get_connection

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

app = FastAPI(title="Financial Operations Agent API")
initialize_database()

class TransactionRequest(BaseModel):
    customer_id: str
    amount: float
    country: str

class TransactionResponse(BaseModel):
    decision: str
    reason: str
    customer_id: str
    amount: float
    country: str

class NaturalLanguageRequest(BaseModel):
    message: str

@app.get("/health")
def health_check():
    return {"status": "running", "service": "Financial Operations Agent"}

@app.post("/transaction/validate", response_model=TransactionResponse)
def validate_transaction(request: TransactionRequest):
    result = run_agent(request.customer_id, request.amount, request.country)
    final_upper = result.upper()
    if "DENIED" in final_upper:
        decision = "DENIED"
    elif "APPROVED" in final_upper:
        decision = "APPROVED"
    else:
        decision = "UNCLEAR"
    return TransactionResponse(
        decision=decision,
        reason=result,
        customer_id=request.customer_id,
        amount=request.amount,
        country=request.country
    )

@app.post("/transaction/chat")
def chat_transaction(request: NaturalLanguageRequest):
    messages = [{"role": "user", "content": request.message}]
    last_customer_id = "UNKNOWN"
    last_amount = 0
    last_country = "UNKNOWN"

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=tools,
            system=system_prompt,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            final_answer = response.content[0].text
            final_upper = final_answer.upper()
            if "DENIED" in final_upper:
                decision = "DENIED"
            elif "APPROVED" in final_upper:
                decision = "APPROVED"
            else:
                decision = "UNCLEAR"
            log_transaction(last_customer_id, last_amount, last_country, decision, final_answer[:200])
            return {
                "decision": decision,
                "reason": final_answer,
                "customer_id": last_customer_id,
                "amount": last_amount,
                "country": last_country
            }

        if response.stop_reason == "tool_use":
            tool_use_block = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input

            if tool_name == "check_transaction_limit":
                last_customer_id = tool_input["customer_id"]
                last_amount = tool_input["amount"]
                tool_result = check_transaction_limit(tool_input["customer_id"], tool_input["amount"])
            elif tool_name == "check_compliance_rules":
                last_country = tool_input["country_to"]
                tool_result = check_compliance_rules(tool_input["country_to"], tool_input["amount"])

            messages.append({"role": "assistant", "content": [tool_use_block]})
            messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use_block.id, "content": tool_result}]})