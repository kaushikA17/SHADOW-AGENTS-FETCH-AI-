"""Module 2: Quotation generator. Output follows the Scout<->Grid contract."""
from catalogue import SUPPLIER_NAME, get_product
from delivery import delivery_report


def _base(request_id, product, quantity, status, **extra):
    msg = {
        "message_type": "SUPPLIER_QUOTATION",
        "request_id": request_id,
        "supplier": SUPPLIER_NAME,
        "product": product,
        "quantity": quantity,
        "unit_price": 0,
        "total_price": 0,
        "delivery_days": 0,
        "status": status,
    }
    msg.update(extra)
    return msg


def build_quotation(request_id, product, quantity, unit_price, deadline_days=None, note=None) -> dict:
    """Quote a given unit price (used by both the list quote and negotiation)."""
    item = get_product(product)
    if item is None:
        return _base(request_id, product, quantity, "PRODUCT_NOT_FOUND")

    if not isinstance(quantity, int) or quantity <= 0:
        return _base(request_id, product, quantity, "INVALID_QUANTITY")

    if quantity < item["min_order_quantity"]:
        return _base(request_id, item["name"].lower(), quantity, "BELOW_MIN_ORDER_QUANTITY",
                     min_order_quantity=item["min_order_quantity"])

    report = delivery_report(product, quantity, deadline_days)
    avail = item["available_quantity"]

    if avail <= 0:
        status, qty_quoted = "OUT_OF_STOCK", 0
    elif avail < quantity:
        status, qty_quoted = "PARTIAL_OFFER", avail
    elif not report["deadline_achievable"]:
        status, qty_quoted = "OFFER_AVAILABLE_LATE", quantity
    else:
        status, qty_quoted = "OFFER_AVAILABLE", quantity

    msg = _base(request_id, item["name"].lower(), quantity, status)
    msg.update(
        unit_price=unit_price,
        total_price=unit_price * qty_quoted,
        delivery_days=report["estimated_delivery_days"],
        available_quantity=avail,
        quoted_quantity=qty_quoted,
        estimated_delivery_date=report["estimated_delivery_date"],
        simulated=True,  # demo data, not a real supplier offer
    )
    if note:
        msg["note"] = note
    return msg


def generate_quotation(request: dict) -> dict:
    item = get_product(request.get("product", ""))
    unit_price = item["unit_price"] if item else 0
    return build_quotation(
        request.get("request_id"),
        request.get("product"),
        request.get("quantity"),
        unit_price,
        request.get("deadline_days", request.get("required_delivery_days")),
    )
