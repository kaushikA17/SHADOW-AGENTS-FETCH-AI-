import json

import pytest

import asi
import orders
from grid import handle_message, handle_text


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    orders.reset()
    monkeypatch.delenv("ASI_ONE_API_KEY", raising=False)  # tests never call ASI:One
    monkeypatch.delenv("ASI1_API_KEY", raising=False)


def req(**kw):
    base = {"message_type": "PROCUREMENT_REQUEST", "request_id": "R1", "product": "bedsheets",
            "quantity": 62, "deadline_days": 5}
    base.update(kw)
    return base


def order(**kw):
    base = {"message_type": "PURCHASE_ORDER", "order_id": "ORD1", "request_id": "R1",
            "product": "bedsheets", "quantity": 62, "agreed_unit_price": 350, "buyer_approved": True}
    base.update(kw)
    return base


# ---- quotations & negotiation ----

def test_quote():
    q = handle_message(req())
    assert q["status"] == "OFFER_AVAILABLE"
    assert q["unit_price"] == 350 and q["total_price"] == 21700 and q["delivery_days"] == 4
    assert q["simulated"] is True


def test_partial_and_unknown():
    assert handle_message(req(quantity=600))["status"] == "PARTIAL_OFFER"
    assert handle_message(req(product="laptops"))["status"] == "PRODUCT_NOT_FOUND"
    assert handle_message(req(quantity=2))["status"] == "BELOW_MIN_ORDER_QUANTITY"


def test_late_delivery():
    assert handle_message(req(deadline_days=1))["status"] == "OFFER_AVAILABLE_LATE"


def test_negotiation_never_below_floor():
    for offer in (1, 200, 300, 315, 329, 340):
        for rnd in (1, 2, 3):
            q = handle_message(req(message_type="NEGOTIATION_REQUEST",
                                   offered_unit_price=offer, round=rnd))
            assert q["unit_price"] >= 315


def test_negotiation_rounds():
    r1 = handle_message(req(message_type="NEGOTIATION_REQUEST", offered_unit_price=300))
    assert r1["unit_price"] == 329 and r1["negotiation_status"] == "COUNTEROFFER"
    r2 = handle_message(req(message_type="NEGOTIATION_REQUEST", offered_unit_price=300, round=2))
    assert r2["unit_price"] == 315 and r2["final_offer"]
    ok = handle_message(req(message_type="NEGOTIATION_REQUEST", offered_unit_price=335))
    assert ok["negotiation_status"] == "OFFER_ACCEPTED" and ok["unit_price"] == 335


def test_bad_messages():
    assert handle_message({"message_type": "HELLO"})["status"] == "UNKNOWN_MESSAGE_TYPE"
    assert handle_message({"message_type": "PROCUREMENT_REQUEST"})["status"] == "MISSING_FIELDS"
    assert handle_message({"message_type": "PURCHASE_ORDER"})["status"] == "MISSING_FIELDS"


# ---- orders ----

def test_order_accepted_after_quote():
    handle_message(req())
    c = handle_message(order())
    assert c["message_type"] == "ORDER_CONFIRMATION" and c["status"] == "ORDER_ACCEPTED"
    assert c["total_price"] == 21700 and c["delivery_days"] == 4 and c["simulated"] is True
    st = handle_message({"message_type": "ORDER_STATUS_REQUEST", "order_id": "ORD1"})
    assert st["order_status"] == "ACCEPTED"


def test_order_without_quote_is_rejected():
    c = handle_message(order())
    assert c["status"] == "ORDER_REJECTED" and c["reason"] == "NO_VALID_QUOTE"
    st = handle_message({"message_type": "ORDER_STATUS_REQUEST", "order_id": "ORD1"})
    assert st["order_status"] == "REJECTED"


def test_order_needs_buyer_approval():
    handle_message(req())
    assert handle_message(order(buyer_approved=False))["reason"] == "BUYER_APPROVAL_MISSING"
    bare = order()
    del bare["buyer_approved"]
    assert handle_message(bare)["reason"] == "BUYER_APPROVAL_MISSING"


def test_order_price_must_be_a_quoted_price():
    handle_message(req())
    assert handle_message(order(agreed_unit_price=100))["reason"] == "PRICE_NOT_QUOTED"


def test_order_at_negotiated_price():
    handle_message(req(message_type="NEGOTIATION_REQUEST", offered_unit_price=300, round=2))
    assert handle_message(order(agreed_unit_price=300))["reason"] == "PRICE_NOT_QUOTED"
    c = handle_message(order(agreed_unit_price=315))
    assert c["status"] == "ORDER_ACCEPTED" and c["total_price"] == 315 * 62


def test_order_stock_moq_and_deadline():
    assert handle_message(order(quantity=600))["reason"] == "INSUFFICIENT_STOCK"
    assert handle_message(order(quantity=2))["reason"] == "BELOW_MIN_ORDER_QUANTITY"
    handle_message(req())
    assert handle_message(order(deadline_days=1))["reason"] == "DEADLINE_NOT_ACHIEVABLE"


def test_duplicate_order_not_accepted_twice():
    handle_message(req())
    handle_message(order())
    again = handle_message(order())
    assert again["status"] == "ORDER_ACCEPTED" and again["duplicate"] is True
    assert len(orders.ORDERS) == 1


def test_status_unknown_and_manual_update():
    assert handle_message({"message_type": "ORDER_STATUS_REQUEST",
                           "order_id": "NOPE"})["order_status"] == "NOT_FOUND"
    handle_message(req())
    handle_message(order())
    orders.set_order_status("ORD1", "dispatched")
    st = handle_message({"message_type": "ORDER_STATUS_REQUEST", "order_id": "ORD1"})
    assert st["order_status"] == "DISPATCHED"
    with pytest.raises(ValueError):
        orders.set_order_status("ORD1", "TELEPORTED")
    handle_message(order(order_id="ORD2", agreed_unit_price=1))  # rejected
    with pytest.raises(ValueError):
        orders.set_order_status("ORD2", "DISPATCHED")


# ---- text / ASI:One fallback ----

def test_json_text_roundtrip():
    out = json.loads(handle_text(json.dumps(req())))
    assert out["status"] == "OFFER_AVAILABLE"


def test_plain_english_quote_without_asi_key():
    out = handle_text("We need 62 bedsheets within 5 days")
    assert "Simulated" in out and '"status": "OFFER_AVAILABLE"' in out and "21,700" in out


def test_plain_english_cannot_place_orders():
    out = handle_text("Please place an order for 62 bedsheets, order ORD77, I approve")
    assert "ORDER_CONFIRMATION" not in out
    assert orders.ORDERS == {}


def test_plain_english_status_and_missing_details():
    handle_message(req())
    handle_message(order())
    assert "ACCEPTED" in handle_text("What is the status of order ORD1?")
    assert "MISSING_FIELDS" in handle_text("I need towels")


# ---- Scout's protocol (request_type / quoted | accepted | rejected) ----

def scout_req(**kw):
    base = {"request_id": "unique-order-id", "request_type": "purchase_request",
            "product": "bedsheets", "quantity": 500, "delivery_location": "Bangalore",
            "delivery_days": 5}
    base.update(kw)
    return base


def scout_order(**kw):
    base = {"request_id": "unique-order-id", "request_type": "order_request"}
    base.update(kw)
    return base


def test_scout_quote_matches_protocol():
    r = handle_message(scout_req())
    expected = {"request_id": "unique-order-id", "supplier_name": "Demo Supplier", "status": "quoted",
                "unit_price": 350, "total_price": 175000, "available_quantity": 500,
                "estimated_delivery_days": 4}
    assert {k: r[k] for k in expected} == expected
    assert r["simulated"] is True and r["meets_deadline"] is True


def test_scout_quote_late_partial_and_rejections():
    assert handle_message(scout_req(delivery_days=1))["meets_deadline"] is False
    partial = handle_message(scout_req(quantity=600))
    assert partial["status"] == "quoted" and partial["partial"] is True
    assert partial["quoted_quantity"] == 500 and partial["total_price"] == 175000
    r = handle_message(scout_req(product="laptops"))
    assert r["status"] == "rejected" and r["reason"] == "PRODUCT_NOT_FOUND"
    assert handle_message(scout_req(quantity=2))["status"] == "rejected"
    assert handle_message({"request_id": "X", "request_type": "purchase_request"})["reason"] == "MISSING_FIELDS"


def test_scout_order_accepted_with_only_request_id():
    handle_message(scout_req())
    r = handle_message(scout_order())
    assert r["status"] == "accepted" and r["request_id"] == "unique-order-id"
    assert r["unit_price"] == 350 and r["total_price"] == 175000 and r["estimated_delivery_days"] == 4
    assert r["supplier_name"] == "Demo Supplier" and r["simulated"] is True


def test_scout_order_rejections():
    r = handle_message(scout_order())  # never quoted
    assert r["status"] == "rejected" and r["reason"] == "NO_VALID_QUOTE"
    handle_message(scout_req())
    assert handle_message(scout_order(unit_price=100))["reason"] == "PRICE_NOT_QUOTED"
    assert handle_message(scout_order(buyer_approved=False))["reason"] == "BUYER_APPROVAL_MISSING"
    assert orders.ORDERS["unique-order-id"]["status"] == "ORDER_REJECTED"


def test_scout_order_not_accepted_twice_and_status():
    handle_message(scout_req())
    handle_message(scout_order())
    again = handle_message(scout_order())
    assert again["status"] == "accepted"
    st = handle_message({"request_id": "unique-order-id", "request_type": "order_status"})
    assert st["status"] == "accepted"
    orders.set_order_status("unique-order-id", "DISPATCHED")
    assert handle_message({"request_id": "unique-order-id", "request_type": "order_status"})["status"] == "dispatched"
    assert handle_message({"request_id": "nope", "request_type": "order_status"})["status"] == "not_found"


def test_scout_every_response_has_request_id():
    for p in (scout_req(), scout_req(product="x"), scout_order(), scout_order(request_id="Z"),
              {"request_id": "Q", "request_type": "weird"},
              {"request_id": "Q", "request_type": "order_status"}):
        r = handle_message(p)
        assert r["request_id"] == p["request_id"] and r["supplier_name"] == "Demo Supplier"


def test_asi_number_guard():
    assert asi._numbers("Rs 21,700 for 62") == {"21700", "62"}
    assert asi._numbers("Rs 21,000") - asi._numbers("Rs 21,700") != set()
