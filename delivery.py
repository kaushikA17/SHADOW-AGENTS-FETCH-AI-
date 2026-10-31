"""Module 4: Delivery intelligence."""
from datetime import date, timedelta

from catalogue import get_product


def delivery_report(product: str, quantity: int, deadline_days=None, today=None) -> dict:
    item = get_product(product)
    if item is None:
        return {"fulfilment": "NOT_POSSIBLE", "reason": "PRODUCT_NOT_FOUND"}

    today = today or date.today()
    available = item["available_quantity"]
    est_days = item["delivery_days"]
    deliverable_qty = min(quantity, available)

    if available >= quantity:
        fulfilment = "POSSIBLE"
    elif available > 0:
        fulfilment = "PARTIAL"
    else:
        fulfilment = "NOT_POSSIBLE"

    deadline_ok = deadline_days is None or est_days <= deadline_days

    return {
        "product": item["name"],
        "requested": quantity,
        "available": available,
        "deliverable_quantity": deliverable_qty,
        "estimated_delivery_days": est_days,
        "estimated_delivery_date": (today + timedelta(days=est_days)).isoformat(),
        "deadline_achievable": deadline_ok,
        "fulfilment": fulfilment,
    }


def format_report(r: dict) -> str:
    if "reason" in r:
        return f"GRID DELIVERY REPORT\n\nFulfilment: {r['fulfilment']} ({r['reason']})"
    return (
        "GRID DELIVERY REPORT\n\n"
        f"Product: {r['product']}\n"
        f"Requested: {r['requested']}\n"
        f"Available: {r['available']}\n"
        f"Delivery estimate: {r['estimated_delivery_days']} days "
        f"({r['estimated_delivery_date']})\n"
        f"Deadline achievable: {'Yes' if r['deadline_achievable'] else 'No'}\n"
        f"Fulfilment: {r['fulfilment'].capitalize()}"
    )
