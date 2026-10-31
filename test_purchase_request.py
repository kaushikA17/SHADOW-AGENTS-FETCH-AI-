from purchase_request import extract_purchase_request
from order_manager import create_order_request

message = """
I need 500 bedsheets for my hotel in Bangalore.
They must be delivered within 5 days.
"""

# Step 1: Extract buyer requirements
purchase_data = extract_purchase_request(message)

# Step 2: Generate structured order request
order = create_order_request(purchase_data)

print("\nSCOUT GENERATED ORDER")
print("=====================")

for key, value in order.items():
    print(f"{key}: {value}")