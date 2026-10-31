"""Scout <-> Grid protocol (Scout's format: request_type / status quoted|accepted|rejected).

Every response includes the original request_id. All data is SIMULATED.

  purchase_request -> status "quoted" (or "rejected" if Grid cannot quote)
  order_request    -> status "accepted" or "rejected"
  order_status     -> status "accepted" / "rejected" / "not_found" / manual ("dispatched", ...)

Scout should send order_request only AFTER the human manager approves. An order submission
counts as that approval unless it explicitly says buyer_approved / approved = false.
"""
from catalogue import SUPPLIER_NAME
from orders import QUOTES, order_status, place_order, record_quote
from quotation import generate_quotation

ORDER_TYPES = {"order_request", "submit_order", "order", "purchase_order", "place_order", "order_submission"}
STATUS_TYPES = {"order_status", "status_request", "status_check", "get_order_status"}

SIM_NOTE = "SIMULATED supplier data for the prototype. Not real availability or delivery confirmation."


def _base(request_id, status, **extra):
    msg = {"request_id": request_id, "supplier_name": SUPPLIER_NAME, "status": status}
    msg.update(extra)
    return msg


def _rejected(request_id, reason, detail=None, **extra):
    return _base(request_id, "rejected", reason=reason, detail=detail or reason,
                 simulated=True, note=SIM_NOTE, **extra)


def handle_scout(payload: dict) -> dict:
    rid = payload.get("request_id")
    rtype = str(payload.get("request_type", "")).strip().lower()

    if rid is None:
        return _rejected(None, "MISSING_REQUEST_ID", "request_id is required.")
    if rtype == "purchase_request":
        return _quote(rid, payload)
    if rtype in ORDER_TYPES:
        return _order(rid, payload)
    if rtype in STATUS_TYPES:
        return _status(rid)
    return _rejected(rid, "UNKNOWN_REQUEST_TYPE", f"Unsupported request_type: {payload.get('request_type')!r}")


def _quote(rid, p):
    missing = [f for f in ("product", "quantity") if f not in p]
    if missing:
        return _rejected(rid, "MISSING_FIELDS", "Missing: " + ", ".join(missing))

    q = generate_quotation({
        "request_id": rid,
        "product": p["product"],
        "quantity": p["quantity"],
        "deadline_days": p.get("delivery_days", p.get("deadline_days")),
    })
    status = q["status"]
    if status in ("OFFER_AVAILABLE", "OFFER_AVAILABLE_LATE", "PARTIAL_OFFER"):
        record_quote(q)  # only full offers are recorded; partials cannot be ordered
        resp = _base(
            rid, "quoted",
            product=q["product"],
            quantity=p["quantity"],
            unit_price=q["unit_price"],
            total_price=q["total_price"],
            available_quantity=q["available_quantity"],
            estimated_delivery_days=q["delivery_days"],
            meets_deadline=status != "OFFER_AVAILABLE_LATE",
            simulated=True,
            note=SIM_NOTE,
        )
        if p.get("delivery_location"):
            resp["delivery_location"] = p["delivery_location"]
        if status == "PARTIAL_OFFER":
            resp.update(partial=True, quoted_quantity=q["quoted_quantity"],
                        note=SIM_NOTE + " Only part of the requested quantity is available; "
                                        "total_price covers quoted_quantity.")
        return resp
    detail = {"PRODUCT_NOT_FOUND": "Grid does not stock this product.",
              "BELOW_MIN_ORDER_QUANTITY": f"Minimum order quantity is {q.get('min_order_quantity')}.",
              "INVALID_QUANTITY": "Quantity must be a positive whole number.",
              "OUT_OF_STOCK": "Out of stock."}.get(status, status)
    return _rejected(rid, status, detail)


def _order(rid, p):
    quotes = QUOTES.get(rid, [])
    last = quotes[-1] if quotes else None
    product = p.get("product") or (last and last["product"])
    quantity = p.get("quantity", last and last["quantity"])
    price = p.get("unit_price", p.get("agreed_unit_price", last and last["unit_price"]))
    if product is None or quantity is None or price is None:
        return _rejected(rid, "NO_VALID_QUOTE", "Grid has not issued a quotation for this request_id.")

    order = {
        "order_id": rid,
        "request_id": rid,
        "product": product,
        "quantity": quantity,
        "agreed_unit_price": price,
        "buyer_approved": p.get("buyer_approved", p.get("approved", True)) is True,
    }
    if "delivery_days" in p:
        order["deadline_days"] = p["delivery_days"]
    c = place_order(order)

    if c["status"] == "ORDER_ACCEPTED":
        return _base(
            rid, "accepted",
            product=c["product"],
            quantity=c["quantity"],
            unit_price=c["unit_price"],
            total_price=c["total_price"],
            estimated_delivery_days=c["delivery_days"],
            estimated_delivery_date=c["estimated_delivery_date"],
            simulated=True,
            note=SIM_NOTE,
        )
    return _rejected(rid, c["reason"], c.get("detail"))


def _status(rid):
    s = order_status({"order_id": rid})
    return _base(rid, s["order_status"].lower(), simulated=True,
                 note=s.get("note", SIM_NOTE), **({"reason": s["reason"]} if "reason" in s else {}))
