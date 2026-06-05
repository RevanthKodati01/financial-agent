import os
from dotenv import load_dotenv
import anthropic
from datetime import datetime
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
system_prompt = """You are a financial operations assistant for a payments company.

For EVERY transaction request, you MUST always call both tools in this order:
1. First call check_transaction_limit to verify the customer limit
2. Then ALWAYS call check_compliance_rules to verify the destination country

Never skip either check. Never rely on your own knowledge for compliance decisions.
Only give a final answer after both tools have been called which includes APPROVED or DENIED."""
# ---- TOOL DEFINITION ----
tools = [
    {
        "name": "check_transaction_limit",
        "description": "Checks if a transaction amount is within the allowed limit for a customer",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique customer ID"
                },
                "amount": {
                    "type": "number",
                    "description": "The transaction amount in USD"
                }
            },
            "required": ["customer_id", "amount"]
        }
    },
    {
        "name":"check_compliance_rules",
        "description": "Checks if a transaction amount is within the allowed limit to a country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country_to": {
                    "type": "string",
                    "description": "The country to which the transaction is being sent"
                },
                "amount": {
                    "type": "number",
                    "description": "The transaction amount in USD"
                }
            },
            "required": ["country_to", "amount"]
        }
    }
]

# ---- TOOL IMPLEMENTATION ----
from database import get_connection, log_transaction

def check_transaction_limit(customer_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT customer_id, name, transaction_limit, status FROM customers WHERE customer_id = ?",
        (customer_id,)
    )
    customer = cursor.fetchone()
    conn.close()
    
    if not customer:
        return f"DENIED: Customer {customer_id} does not exist in the system."
    
    if customer["status"] != "active":
        return f"DENIED: Customer {customer_id} account is suspended."
    
    if amount <= customer["transaction_limit"]:
        return f"APPROVED: Customer {customer['name']} has a limit of ${customer['transaction_limit']}. Transaction of ${amount} is within limit."
    else:
        return f"DENIED: Customer {customer['name']} has a limit of ${customer['transaction_limit']}. Transaction of ${amount} exceeds limit."


def check_compliance_rules(country_to, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT country_name, risk_level, max_amount FROM countries WHERE country_name = ?",
        (country_to,)
    )
    country = cursor.fetchone()
    conn.close()
    
    if not country:
        return f"APPROVED: No specific restrictions found for {country_to}. Transaction allowed."
    
    if country["risk_level"] == "restricted":
        return f"DENIED: Transactions to {country_to} are strictly prohibited."
    
    if country["risk_level"] == "high_risk":
        if amount > country["max_amount"]:
            return f"DENIED: Transaction to {country_to} exceeds the ${country['max_amount']} limit for high-risk countries."
        else:
            return f"APPROVED WITH FLAG: Transaction to {country_to} is within limits but flagged for review."
    
    return f"APPROVED: Transaction to {country_to} is allowed."

def run_agent(customer_id,amount,country):
    # ---- AGENT LOOP ----
    user_message = f"I want to send ${amount} to {country}. My customer ID is {customer_id}."
    messages = [{"role": "user", "content": user_message}]

    # Keep looping until Claude has all the information it needs
    while True:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=tools,
            system=system_prompt,
            messages=messages
        )
        
        # If Claude is done calling tools, print final answer and exit
        if response.stop_reason == "end_turn":
            messages.append({"role": "assistant", "content": response.content})
            final_answer = response.content[0].text
            # Log the transaction
            final_upper = final_answer.upper()
            if "DENIED" in final_upper:
                decision = "DENIED"
            elif "APPROVED" in final_upper:
                decision = "APPROVED"
            else:
                decision = "UNKNOWN"
            log_transaction(customer_id, amount, country, decision, final_answer[:200])
            return final_answer
            
        
        # Claude wants to call a tool
        if response.stop_reason == "tool_use":
            tool_use_block = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input
            
            print(f"Claude is calling tool: {tool_name}")
            print(f"With parameters: {tool_input}\n")
            
            # Run the right tool
            if tool_name == "check_transaction_limit":
                tool_result = check_transaction_limit(
                    tool_input["customer_id"],
                    tool_input["amount"]
                )
            elif tool_name == "check_compliance_rules":
                tool_result = check_compliance_rules(
                    tool_input["country_to"],
                    tool_input["amount"]
                )
            
            print(f"Tool result: {tool_result}\n")
            
            # Add tool call and result to messages
            messages.append({"role": "assistant", "content": [tool_use_block]})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": tool_result
                    }
                ]
            })
            
if __name__ == "__main__":
    messages = []
    print("Financial Operations Agent ready. Type your request.\n")
    while True:
        user_message = input("You: ")
        if not user_message.strip():
            print("Please enter a message.")
            continue
        messages.append({"role": "user", "content": user_message})
        while True:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                tools=tools,
                system=system_prompt,
                messages=messages
            )
            if response.stop_reason == "end_turn":
                messages.append({"role": "assistant", "content": response.content})
                print(f"Claude: {response.content[0].text}\n")
                break
            if response.stop_reason == "tool_use":
                tool_use_block = next(block for block in response.content if block.type == "tool_use")
                tool_name = tool_use_block.name
                tool_input = tool_use_block.input
                if tool_name == "check_transaction_limit":
                    tool_result = check_transaction_limit(tool_input["customer_id"], tool_input["amount"])
                elif tool_name == "check_compliance_rules":
                    tool_result = check_compliance_rules(tool_input["country_to"], tool_input["amount"])
                messages.append({"role": "assistant", "content": [tool_use_block]})
                messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use_block.id, "content": tool_result}]})