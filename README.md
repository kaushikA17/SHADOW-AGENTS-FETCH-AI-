# GRID: Supplier AI Agent (prototype)

All supplier data is **SIMULATED**. Orders are held in memory only (no database, no live tracking).
GRID confirms an order only by returning `ORDER_ACCEPTED`.

## Scout protocol (primary; see protocol.py)

Every response includes the original `request_id` and `supplier_name: "Demo Supplier"`. All data is simulated.

| Scout sends (`request_type`) | Fields | Grid replies (`status`) |
| --- | --- | --- |
| `purchase_request` | request_id, product, quantity, delivery_location, delivery_days | `quoted` (unit_price, total_price, available_quantity, estimated_delivery_days, meets_deadline) or `rejected` (+ reason) |
| `order_request` | request_id (price/product/quantity optional; taken from the quote) | `accepted` or `rejected` (+ reason) |
| `order_status` | request_id | `accepted`, `rejected`, `not_found`, or a manual value (`processing`, `dispatched`, `delivered`, `cancelled`) |

- An order is accepted only if Grid quoted that request_id, product, quantity and price.
- Send `order_request` only after the human manager approves. A submission counts as approval unless it sets `buyer_approved: false`.
- A quote for more than the available stock returns `quoted` with `partial: true`, `quoted_quantity` and a total for that quantity only.

## Legacy message contract (message_type; JSON carried in A2A text messages)

| Scout sends | Required fields | Grid replies |
| --- | --- | --- |
| `PROCUREMENT_REQUEST` | request_id, product, quantity (optional: delivery_location, deadline_days) | `SUPPLIER_QUOTATION` |
| `NEGOTIATION_REQUEST` | request_id, product, quantity (optional: offered_unit_price, round) | `SUPPLIER_QUOTATION` |
| `PURCHASE_ORDER` | order_id, request_id, product, quantity, agreed_unit_price, **buyer_approved: true** | `ORDER_CONFIRMATION` |
| `ORDER_STATUS_REQUEST` | order_id | `ORDER_STATUS` |
| `DELIVERY_QUERY` | product, quantity | `DELIVERY_REPORT` |

- `SUPPLIER_QUOTATION.status`: `OFFER_AVAILABLE`, `OFFER_AVAILABLE_LATE`, `PARTIAL_OFFER`, `PRODUCT_NOT_FOUND`, `BELOW_MIN_ORDER_QUANTITY`, ...
- `ORDER_CONFIRMATION.status`: `ORDER_ACCEPTED` or `ORDER_REJECTED` (with `reason`, e.g. `NO_VALID_QUOTE`, `PRICE_NOT_QUOTED`, `BUYER_APPROVAL_MISSING`, `INSUFFICIENT_STOCK`).
- An order is accepted only if Grid quoted that price for that request_id, product and quantity.
- `ORDER_STATUS.order_status`: `ACCEPTED`, `REJECTED`, `NOT_FOUND`, or a value set manually by the supplier (`PROCESSING`, `DISPATCHED`, `DELIVERED`, `CANCELLED`).

## ASI:One
`asi.py` uses ASI:One (`ASI_ONE_API_KEY`) only to understand plain-English requests and to word replies.
Prices, accept/reject decisions and stock checks are plain Python. Without a key, Grid uses rule-based fallbacks.

## Run
```
pip install -r requirements.txt
python -m pytest        # logic tests
python grid.py          # local demo: quote -> counteroffer -> order -> status
python grid_a2a.py      # connect to Agentverse (needs .env)
```
