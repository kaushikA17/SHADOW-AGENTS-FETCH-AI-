def approve_order(quotation):

    print("\nSCOUT ORDER APPROVAL")
    print("====================")

    print("Supplier:", quotation["supplier_name"])
    print("Total Price: ₹", quotation["total_price"])
    print("Delivery:", quotation["estimated_delivery_days"], "days")

    decision = input("\nApprove this order? (yes/no): ").strip().lower()

    if decision == "yes":

        return {
            "status": "approved_by_buyer",
            "supplier_name": quotation["supplier_name"],
            "total_price": quotation["total_price"]
        }

    return {
        "status": "rejected_by_buyer",
        "message": "Buyer rejected the quotation."
    }