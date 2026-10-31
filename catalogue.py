"""Module 1: Supplier product catalogue (SIMULATED demo data, not real supplier information)."""

SUPPLIER_NAME = "Demo Supplier"  # name Scout expects in supplier_name
MAX_DISCOUNT_PCT = 10  # hard commercial limit across all products

CATALOGUE = {
    "bedsheets": {
        "product_id": "GRD-BED-001",
        "name": "Bedsheets",
        "unit_price": 350,
        "min_price": 315,  # 10% below list; never go below this
        "available_quantity": 500,
        "min_order_quantity": 10,
        "delivery_days": 4,
        "specs": "Cotton, 300 thread count, king size, white",
    },
    "towels": {
        "product_id": "GRD-TWL-002",
        "name": "Towels",
        "unit_price": 180,
        "min_price": 162,
        "available_quantity": 300,
        "min_order_quantity": 20,
        "delivery_days": 2,
        "specs": "Cotton, 500 GSM, bath size, white",
    },
    "pillows": {
        "product_id": "GRD-PIL-003",
        "name": "Pillows",
        "unit_price": 250,
        "min_price": 225,
        "available_quantity": 200,
        "min_order_quantity": 10,
        "delivery_days": 4,
        "specs": "Microfiber fill, 17x27 in",
    },
    "blankets": {
        "product_id": "GRD-BLK-004",
        "name": "Blankets",
        "unit_price": 650,
        "min_price": 585,
        "available_quantity": 150,
        "min_order_quantity": 5,
        "delivery_days": 5,
        "specs": "Fleece, double bed, grey",
    },
}


def normalize(product: str) -> str:
    return (product or "").strip().lower()


def get_product(product: str):
    """Return catalogue entry or None. Accepts simple singular forms (e.g. 'bedsheet')."""
    key = normalize(product)
    if key in CATALOGUE:
        return CATALOGUE[key]
    if key + "s" in CATALOGUE:
        return CATALOGUE[key + "s"]
    return None


def check_stock(product: str, quantity: int) -> dict:
    item = get_product(product)
    if item is None:
        return {"found": False, "in_stock": False, "available": 0}
    avail = item["available_quantity"]
    return {"found": True, "in_stock": avail >= quantity, "available": avail}
