from quotation_engine import compare_quotations

required_quantity = 500

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
    required_quantity,
    max_delivery_days=5
)

print("\nSCOUT SUPPLIER COMPARISON")
print("=========================")

print("Status:", result["status"])

if result["status"] == "comparison_complete":

    for quote in result["all_quotes"]:
        print("\nSupplier:", quote["supplier_name"])
        print("Unit Price: ₹", quote["unit_price"])
        print("Total Price: ₹", quote["total_price"])
        print("Delivery:", quote["estimated_delivery_days"], "days")

    print("\nRECOMMENDED SUPPLIER:")
    print(result["best_supplier"]["supplier_name"])