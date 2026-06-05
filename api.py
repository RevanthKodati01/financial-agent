from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent
from database import initialize_database

# Initialize the app and database
app = FastAPI(title="Financial Operations Agent API")
initialize_database()

# Define what a transaction request looks like
class TransactionRequest(BaseModel):
    customer_id: str
    amount: float
    country: str

# Define what the response looks like
class TransactionResponse(BaseModel):
    decision: str
    reason: str
    customer_id: str
    amount: float
    country: str

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "running", "service": "Financial Operations Agent"}

# Main transaction endpoint
@app.post("/transaction/validate", response_model=TransactionResponse)
def validate_transaction(request: TransactionRequest):
    result = run_agent(request.customer_id, request.amount, request.country)
    
    # Determine decision
    result_upper = result.upper()
    decision = "DENIED" if "DENIED" in result_upper else "APPROVED"
    
    return TransactionResponse(
        decision=decision,
        reason=result,
        customer_id=request.customer_id,
        amount=request.amount,
        country=request.country
    )