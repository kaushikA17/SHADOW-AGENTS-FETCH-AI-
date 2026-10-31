"""Order handling: accept/reject purchase orders, confirmations, manual status.

In-memory only (prototype: no database, no live inventory or delivery tracking).
GRID confirms an order ONLY by returning ORDER_ACCEPTED from place_order().
"""
from catalogue import SUPPLIER_NAME, get_product
from delivery import delivery_report

QUOTES = {}  # request_id -> [{"product", "quantity", "unit_price"}, ...] that Grid has offered
ORDERS = {}  # order_id -> latest confirmation/rejection dict

# Statuses a human operator at the supplier may set by hand (never set automatically).
OPERATOR_STATUSES = {"PROCESSING", "DISPATCHED", "DELIVERED", "CANCELLED"}

STATUS_NOTE = "Manual status update from the supplier. There is no live tracking in this prototype."


def reset():
    QUOTES.clear()
    ORDERS.clear()


def record_quote(quote: dict) -> None:
    """Remember a price Grid has genuinely offered, so an order can only use quoted prices."""
    if quote.get("message_type") != "SUPPLIER_QUOTATION" or quote.get("status") not in (
            "OFFER_AVAILABLE", "OFFER_AVAILABLE_LATE"):
        return
    QUOTES.setdefault(quote["request_id"], []).append({
        "product": quote["product"],
        "quantity": quote["quantity"],
        "unit_price": quote["unit_price"],
    })


def _rejection(payload: dict, reason: str, detail: str) -> dict:
    result = {
        "message_type": "ORDER_CONFIRMATION",
        "order_id": payload.get("order_id"),
        "request_id": payload.get("request_id"),
        "supplier": SUPPLIER_NAME,
        "product": payload.get("product"),
        "quantity": payload.get("quantity"),
        "unit_price": 0,
        "total_price": 0,
        "delivery_days": 0,
        "status": "ORDER_REJECTED",
        "order_status": "REJECTED",
        "reason": reason,
        "detail": detail,
        "simulated": True,
    }
    ORDERS[payload.get("order_id")] = result
    return result


def place_order(payload: dict) -> dict:
    """Evaluate a PURCHASE_ORDER. Returns ORDER_CONFIRMATION (ORDER_ACCEPTED or ORDER_REJECTED)."""
    order_id = payload["order_id"]
    existing = ORDERS.get(order_id)
    if existing and existing["status"] == "ORDER_ACCEPTED":
        return {**existing, "duplicate": True}  # idempotent: never accept the same order twice

    item = get_product(payload["product"])
    if item is None:
        return _rejection(payload, "PRODUCT_NOT_FOUND", "Grid does not stock this product.")

    qty = payload["quantity"]
    if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
        return _rejection(payload, "INVALID_QUANTITY", "Quantity must be a positive whole number.")
    if qty < item["min_order_quantity"]:
        return _rejection(payload, "BELOW_MIN_ORDER_QUANTITY",
                          f"Minimum order quantity is {item['min_order_quantity']}.")
    if qty > item["available_quantity"]:
        return _rejection(payload, "INSUFFICIENT_STOCK",
                          f"Only {item['available_quantity']} units are available.")

    if payload.get("buyer_approved") is not True:
        return _rejection(payload, "BUYER_APPROVAL_MISSING",
                          "Orders need explicit human approval from the buyer (buyer_approved: true).")

    name = item["name"].lower()
    offers = [q for q in QUOTES.get(payload["request_id"], [])
              if q["product"] == name and q["quantity"] == qty]
    if not offers:
        return _rejection(payload, "NO_VALID_QUOTE",
                          "Grid has not issued a quotation for this request, product and quantity.")

    price = payload["agreed_unit_price"]
    if price not in {q["unit_price"] for q in offers}:
        return _rejection(payload, "PRICE_NOT_QUOTED",
                          "The agreed unit price is not a price Grid has offered for this request.")

    report = delivery_report(name, qty, payload.get("deadline_days"))
    if not report["deadline_achievable"]:
        return _rejection(payload, "DEADLINE_NOT_ACHIEVABLE",
                          f"Grid needs about {report['estimated_delivery_days']} days to deliver.")

    confirmation = {
        "message_type": "ORDER_CONFIRMATION",
        "order_id": order_id,
        "request_id": payload["request_id"],
        "supplier": SUPPLIER_NAME,
        "product": name,
        "quantity": qty,
        "unit_price": price,
        "total_price": price * qty,
        "delivery_days": report["estimated_delivery_days"],
        "estimated_delivery_date": report["estimated_delivery_date"],
        "status": "ORDER_ACCEPTED",
        "order_status": "ACCEPTED",
        "simulated": True,  # prototype data, not a real supplier commitment
    }
    ORDERS[order_id] = confirmation
    return confirmation


def order_status(payload: dict) -> dict:
    """Answer ORDER_STATUS_REQUEST from the recorded state. No tracking happens here."""
    order_id = payload["order_id"]
    order = ORDERS.get(order_id)
    result = {
        "message_type": "ORDER_STATUS",
        "order_id": order_id,
        "supplier": SUPPLIER_NAME,
        "simulated": True,
    }
    if order is None:
        result.update(order_status="NOT_FOUND", note="Grid has no order with this ID.")
        return result
    result.update(
        request_id=order["request_id"],
        product=order["product"],
        quantity=order["quantity"],
        order_status=order["order_status"],
        note=STATUS_NOTE,
    )
    if order["status"] == "ORDER_REJECTED":
        result["reason"] = order["reason"]
    return result


def set_order_status(order_id: str, status: str) -> None:
    """Operator-only: manually move an ACCEPTED order forward. Not reachable via messages."""
    status = status.upper()
    if status not in OPERATOR_STATUSES:
        raise ValueError(f"status must be one of {sorted(OPERATOR_STATUSES)}")
    order = ORDERS.get(order_id)
    if order is None or order["status"] != "ORDER_ACCEPTED":
        raise ValueError("only accepted orders can be updated")
    order["order_status"] = status
