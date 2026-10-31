def process_grid_response(response, original_order):

    if response["request_id"] != original_order["request_id"]:
        return {
            "status": "error",
            "message": "Order ID mismatch."
        }

    supplier_status = response["status"]

    if supplier_status == "accepted":
        return {
            "status": "order_confirmed",
            "message": "Grid has accepted the order."
        }

    elif supplier_status == "rejected":
        return {
            "status": "order_rejected",
            "message": "Grid has rejected the order."
        }

    return {
        "status": "pending",
        "message": "Waiting for Grid's response."
    }