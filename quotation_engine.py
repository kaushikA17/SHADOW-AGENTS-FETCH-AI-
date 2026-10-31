def compare_quotations(quotations, required_quantity, max_delivery_days=None):

    valid_quotes = []

    for quote in quotations:

        if quote["available_quantity"] < required_quantity:
            continue

        if (
            max_delivery_days is not None
            and quote["estimated_delivery_days"] > max_delivery_days
        ):
            continue

        if quote["unit_price"] <= 0:
            continue

        if quote["estimated_delivery_days"] < 0:
            continue

        quote["total_price"] = (
            quote["unit_price"] * required_quantity
        )

        valid_quotes.append(quote)

    if not valid_quotes:
        return {
            "status": "no_valid_quotes",
            "message": "No supplier can fulfil this requirement."
        }

    ranked_quotes = sorted(
        valid_quotes,
        key=lambda x: (
            x["total_price"],
            x["estimated_delivery_days"]
        )
    )

    return {
        "status": "comparison_complete",
        "best_supplier": ranked_quotes[0],
        "all_quotes": ranked_quotes
    }