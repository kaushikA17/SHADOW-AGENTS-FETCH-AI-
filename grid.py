"""Grid: AI supplier agent. Main entry point.

handle_message() is transport-agnostic: it takes the JSON payload carried inside an
A2A message and returns the JSON reply. grid_a2a.py wraps it for Agentverse, so the
business logic can be tested without any network.

Flow:  PROCUREMENT_REQUEST -> SUPPLIER_QUOTATION
       (NEGOTIATION_REQUEST -> SUPPLIER_QUOTATION, optional)
       PURCHASE_ORDER -> ORDER_CONFIRMATION (ORDER_ACCEPTED / ORDER_REJECTED)
       ORDER_STATUS_REQUEST -> ORDER_STATUS
All supplier data is SIMULATED prototype data.
"""
import json

import asi
from delivery import delivery_report
from negotiation import negotiate
from orders import order_status, place_order, record_quote
from protocol import handle_scout
from quotation import generate_quotation

REQUIRED_FIELDS = {
    "PROCUREMENT_REQUEST": ["request_id", "product", "quantity"],
    "NEGOTIATION_REQUEST": ["request_id", "product", "quantity"],
    "DELIVERY_QUERY": ["product", "quantity"],
    "PURCHASE_ORDER": ["order_id", "request_id", "product", "quantity", "agreed_unit_price"],
    "ORDER_STATUS_REQUEST": ["order_id"],
}


def handle_message(payload: dict) -> dict:
    if "request_type" in payload and "message_type" not in payload:
        return handle_scout(payload)  # Scout's protocol (see protocol.py)

    mtype = payload.get("message_type")
    if mtype not in REQUIRED_FIELDS:
        return {"message_type": "ERROR", "status": "UNKNOWN_MESSAGE_TYPE", "received": mtype}

    missing = [f for f in REQUIRED_FIELDS[mtype] if f not in payload]
    if missing:
        return {"message_type": "ERROR", "status": "MISSING_FIELDS", "fields": missing}

    if mtype == "PROCUREMENT_REQUEST":
        reply = generate_quotation(payload)
        record_quote(reply)
        return reply
    if mtype == "NEGOTIATION_REQUEST":
        reply = negotiate(payload)
        record_quote(reply)
        return reply
    if mtype == "PURCHASE_ORDER":
        return place_order(payload)
    if mtype == "ORDER_STATUS_REQUEST":
        return order_status(payload)
    return {"message_type": "DELIVERY_REPORT",
            **delivery_report(payload["product"], payload["quantity"], payload.get("deadline_days"))}


def handle_text(text: str) -> str:
    """Text transport. JSON in -> JSON out (Scout). Plain English in -> summary + JSON (humans).

    Free text can ask for quotes, prices, delivery and order status, but can never place
    an order: PURCHASE_ORDER must arrive as structured JSON with buyer_approved: true.
    """
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        payload = None
    if isinstance(payload, dict):
        return json.dumps(handle_message(payload))

    request = asi.parse_request(text)
    if request is None:
        return "Tell me the product and quantity you need, or send a structured JSON request."
    reply = handle_message(request)
    return asi.explain(reply) + "\n\n" + json.dumps(reply)


if __name__ == "__main__":
    def show(label, msg):
        print(f"--- {label}")
        print(json.dumps(msg, indent=2))

    quote = handle_message({"message_type": "PROCUREMENT_REQUEST", "request_id": "REQ001",
                            "product": "bedsheets", "quantity": 62,
                            "delivery_location": "Bangalore", "deadline_days": 5})
    show("Quotation", quote)
    better = handle_message({"message_type": "NEGOTIATION_REQUEST", "request_id": "REQ001",
                             "product": "bedsheets", "quantity": 62, "offered_unit_price": 300})
    show("Counteroffer", better)
    show("Order", handle_message({"message_type": "PURCHASE_ORDER", "order_id": "ORD001",
                                  "request_id": "REQ001", "product": "bedsheets", "quantity": 62,
                                  "agreed_unit_price": better["unit_price"], "buyer_approved": True}))
    show("Status", handle_message({"message_type": "ORDER_STATUS_REQUEST", "order_id": "ORD001"}))
