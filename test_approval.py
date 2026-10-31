from approval_manager import approve_order

quotation = {
    "supplier_name": "Supplier B",
    "total_price": 160000,
    "estimated_delivery_days": 6
}

result = approve_order(quotation)

print("\nORDER RESULT")
print("============")

for key, value in result.items():
    print(f"{key}: {value}")