import uuid


def create_order_request(purchase_data):

    order = {
        "request_id": str(uuid.uuid4()),
        "request_type": "purchase_request",
        "product": purchase_data["product"],
        "quantity": purchase_data["quantity"],
        "delivery_location": purchase_data["delivery_location"],
        "delivery_days": purchase_data["delivery_days"],
        "status": "pending_supplier_quote"
    }

    return order