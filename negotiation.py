"""Module 3: Negotiation engine with hard commercial limits.

Rules:
- Discount allowed depends on quantity (volume tiers).
- Grid never goes below the product's min_price (max 10% off list).
- Round 1 offers the volume-tier price; round 2+ may go to the absolute floor.
"""
import math

from catalogue import MAX_DISCOUNT_PCT, get_product
from quotation import build_quotation

# (min quantity, discount % offered in round 1)
VOLUME_TIERS = [(100, 8), (50, 6), (20, 3), (0, 0)]


def _tier_discount(quantity: int) -> int:
    for min_qty, pct in VOLUME_TIERS:
        if quantity >= min_qty:
            return min(pct, MAX_DISCOUNT_PCT)
    return 0


def _floor_price(item) -> int:
    """Absolute lowest price Grid will ever quote."""
    pct_floor = math.ceil(item["unit_price"] * (1 - MAX_DISCOUNT_PCT / 100))
    return max(item["min_price"], pct_floor)


def negotiate(request: dict) -> dict:
    """request: request_id, product, quantity, offered_unit_price (optional), round (default 1)."""
    request_id = request.get("request_id")
    product = request.get("product")
    quantity = request.get("quantity")
    offer = request.get("offered_unit_price")
    rnd = request.get("round", 1)
    deadline = request.get("deadline_days")

    item = get_product(product)
    if item is None:
        return build_quotation(request_id, product, quantity, 0)

    list_price = item["unit_price"]
    floor = _floor_price(item)
    tier_price = max(floor, math.ceil(list_price * (1 - _tier_discount(quantity) / 100)))
    ceiling = tier_price if rnd <= 1 else floor  # best price available this round

    if offer is None:
        price, outcome = ceiling, "COUNTEROFFER"
        note = f"Listed price is Rs {list_price}. I can offer Rs {price} per unit for this quantity."
    elif offer >= list_price:
        price, outcome, note = list_price, "OFFER_ACCEPTED", "Offer at or above list price; quoting list price."
    elif offer >= ceiling:
        price, outcome, note = offer, "OFFER_ACCEPTED", f"Your price of Rs {offer} per unit is accepted."
    else:
        price, outcome = ceiling, "COUNTEROFFER"
        note = f"I cannot meet Rs {offer}. My best price is Rs {price} per unit."
        if ceiling == floor:
            note += " This is my final offer."

    price = max(price, floor)  # safety net: never below the floor
    q = build_quotation(request_id, product, quantity, price, deadline, note)
    q["negotiation_status"] = outcome
    q["round"] = rnd
    q["final_offer"] = outcome == "OFFER_ACCEPTED" or price == floor
    return q
