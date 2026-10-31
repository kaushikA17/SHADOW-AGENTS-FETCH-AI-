from grid_response import process_grid_response
from order_manager import create_order_request

# Create a sample order
purchase_data = {
    "product": "bedsheets",
    "quantity": 500,
    "delivery_location": "Bangalore",
    "delivery_days": 5
}

order = create_order_request(purchase_data)

# Simulated Grid response
grid_response = {
    "request_id": order["request_id"],
    "status": "accepted"
}

result = process_grid_response(grid_response, order)

print("\nSCOUT - GRID COMMUNICATION TEST")
print("================================")

print("Order ID:", order["request_id"])
print("Grid Response:", grid_response["status"])
print("Final Status:", result["status"])
print("Message:", result["message"])