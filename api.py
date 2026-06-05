import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from pydantic import BaseModel
import anthropic
from agent import run_agent, check_transaction_limit, check_compliance_rules, tools, system_prompt
from database import initialize_database, log_transaction, get_connection

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

app = FastAPI(title="Financial Operations Agent API")
security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, 
        os.getenv("ADMIN_USERNAME", "admin")
    )
    correct_password = secrets.compare_digest(
        credentials.password, 
        os.getenv("ADMIN_PASSWORD", "revanth2026")
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")
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

# ---- ADMIN MODELS ----
class CustomerModel(BaseModel):
    customer_id: str
    name: str
    transaction_limit: float
    status: str = "active"

class CountryModel(BaseModel):
    country_name: str
    risk_level: str  # allowed, high_risk, restricted
    max_amount: float = None

# ---- ADMIN ENDPOINTS ----
@app.get("/admin/customers")
def get_customers(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    customers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"customers": customers}

@app.post("/admin/customers")
def upsert_customer(customer: CustomerModel, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customers (customer_id, name, transaction_limit, status)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(customer_id) DO UPDATE SET
            name=excluded.name,
            transaction_limit=excluded.transaction_limit,
            status=excluded.status
    """, (customer.customer_id, customer.name, customer.transaction_limit, customer.status))
    conn.commit()
    conn.close()
    return {"message": f"Customer {customer.customer_id} saved successfully"}

@app.get("/admin/countries")
def get_countries(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries")
    countries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"countries": countries}

@app.post("/admin/countries")
def upsert_country(country: CountryModel, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO countries (country_name, risk_level, max_amount)
        VALUES (?, ?, ?)
        ON CONFLICT(country_name) DO UPDATE SET
            risk_level=excluded.risk_level,
            max_amount=excluded.max_amount
    """, (country.country_name, country.risk_level, country.max_amount))
    conn.commit()
    conn.close()
    return {"message": f"Country {country.country_name} saved successfully"}

@app.get("/admin")
def admin_panel(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    return FileResponse("static/admin.html")

@app.get("/admin/transactions")
def get_transactions(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transaction_history ORDER BY transaction_id DESC LIMIT 50")
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"transactions": transactions}