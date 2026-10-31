from purchase_request import extract_purchase_request
from order_manager import create_order_request
from quotation_engine import compare_quotations
from approval_manager import approve_order
from grid_response import process_grid_response


# STEP 1: Buyer requirement
message = """
I need 500 bedsheets for my hotel in Bangalore.
They must be delivered within 5 days.
"""

print("\n========== SCOUT PROCUREMENT SYSTEM ==========")


# STEP 2: Extract purchase details using ASI:One
print("\n[1] Extracting buyer requirements...")

purchase_data = extract_purchase_request(message)

print(purchase_data)


# STEP 3: Validate required information
required_fields = [
    "product",
    "quantity",
    "delivery_location",
    "delivery_days"
]

if any(purchase_data.get(field) is None for field in required_fields):
    print("\nMissing purchase information. Please provide all details.")
    raise SystemExit


# STEP 4: Create purchase request
print("\n[2] Creating purchase request...")

order = create_order_request(purchase_data)

print("Request ID:", order["request_id"])
print("Status:", order["status"])


# STEP 5: Simulated supplier quotations
print("\n[3] Comparing supplier quotations...")

# SIMULATED DATA — NOT REAL SUPPLIER OFFERS

quotations = [
    {
        "supplier_name": "Supplier A",
        "unit_price": 350,
        "available_quantity": 600,
        "estimated_delivery_days": 4
    },
    {
        "supplier_name": "Supplier B",
        "unit_price": 320,
        "available_quantity": 500,
        "estimated_delivery_days": 6
    },
    {
        "supplier_name": "Supplier C",
        "unit_price": 300,
        "available_quantity": 300,
        "estimated_delivery_days": 3
    }
]

result = compare_quotations(
    quotations,
    purchase_data["quantity"],
    max_delivery_days=purchase_data["delivery_days"]
)

if result["status"] != "comparison_complete":
    print(result["message"])
    raise SystemExit


# STEP 6: Display quotations
for quote in result["all_quotes"]:
    print("\nSupplier:", quote["supplier_name"])
    print("Unit price: ₹", quote["unit_price"])
    print("Total price: ₹", quote["total_price"])
    print("Delivery:", quote["estimated_delivery_days"], "days")


# STEP 7: Buyer approval
print("\n[4] Buyer approval required...")

approval = approve_order(result["best_supplier"])

if approval["status"] != "approved_by_buyer":
    print("\nOrder stopped:", approval["status"])
    raise SystemExit


# STEP 8: Simulate Grid supplier response
print("\n[5] Waiting for Grid supplier response...")

# SIMULATED RESPONSE — NOT A LIVE A2A MESSAGE

grid_response = {
    "request_id": order["request_id"],
    "status": "accepted"
}

final_result = process_grid_response(
    grid_response,
    order
)


# STEP 9: Final status
print("\n========== FINAL ORDER STATUS ==========")

print("Buyer approval:", approval["status"])
print("Supplier response:", grid_response["status"])
print("Final status:", final_result["status"])
print("Message:", final_result["message"])