# SCOUT INVENTORY INTELLIGENCE

inventory = {
    "bedsheets": {
        "available": 138,
        "required": 200
    },
    "towels": {
        "available": 85,
        "required": 150
    },
    "pillows": {
        "available": 120,
        "required": 100
    },
    "blankets": {
        "available": 40,
        "required": 90
    }
}


def check_inventory():

    print("\nSCOUT INVENTORY REPORT")
    print("=" * 40)

    total_shortage = 0

    for item, data in inventory.items():

        available = data["available"]
        required = data["required"]

        shortage = max(0, required - available)

        total_shortage += shortage

        print(f"\nItem: {item.title()}")
        print(f"Available: {available}")
        print(f"Required: {required}")
        print(f"Shortage: {shortage}")

        if shortage > 0:
            print("Status: PROCUREMENT REQUIRED")
        else:
            print("Status: STOCK SUFFICIENT")

    print("\n" + "=" * 40)
    print(f"TOTAL UNITS TO PROCURE: {total_shortage}")


if __name__ == "__main__":
    check_inventory()