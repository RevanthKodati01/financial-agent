from agent import run_agent

test_cases = [
    {"customer_id": "C-1042", "amount": 5000,  "country": "Mexico",  "expected": "APPROVED"},
    {"customer_id": "C-1042", "amount": 15000, "country": "Mexico",  "expected": "DENIED"},
    {"customer_id": "C-1042", "amount": 5000,  "country": "Iran",    "expected": "DENIED"},
    {"customer_id": "C-9999", "amount": 5000,  "country": "Mexico",  "expected": "DENIED"},
    {"customer_id": "C-2077", "amount": 30000, "country": "Russia",  "expected": "DENIED"},
    {"customer_id": "C-1042", "amount": 25000, "country": "Poland",  "expected": "DENIED"},
    {"customer_id": "C-1042", "amount": 25000, "country": "Russia",  "expected": "DENIED"},
    {"customer_id": "C-1042", "amount": 5000,  "country": "Russia",  "expected": "APPROVED"},
    {"customer_id": "C-1043", "amount": 25000, "country": "Russia",  "expected": "DENIED"},
    {"customer_id": "C-1042", "amount": 5000,  "country": "Cuba",    "expected": "DENIED"},
]

passed = 0
failed = 0

print("Running eval harness...\n")
print("-" * 60)

for i, test in enumerate(test_cases):
    result = run_agent(test["customer_id"], test["amount"], test["country"])
    
    # Check if expected word appears in result
    if test["expected"] in result.upper():
        status = "PASS ✅"
        passed += 1
    else:
        status = "FAIL ❌"
        failed += 1
    
    print(f"Test {i+1}: {test['customer_id']} | ${test['amount']} | {test['country']}")
    print(f"Expected: {test['expected']} | Result: {status}")
    print()

print("-" * 60)
print(f"Score: {passed}/{len(test_cases)} passed")
print(f"Accuracy: {round(passed/len(test_cases)*100)}%")