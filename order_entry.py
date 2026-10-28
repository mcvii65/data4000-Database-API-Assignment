"""Interactive command-line order entry using the Supabase Data API."""

from decimal import Decimal
import re

import httpx
from postgrest.exceptions import APIError

from database import create_order, get_client, get_customers, get_products


def report_supabase_api_error(action, error):
    print(f"Supabase could not {action}.")
    if error.code:
        print(f"API error code: {error.code}")
    if error.message:
        # Only show the API's short message; omit details and hints that may contain data.
        message = re.sub(
            r"(?i)\b(sb_secret|sb_publishable)_[A-Za-z0-9_-]+",
            r"\1_[redacted]",
            error.message,
        )
        print(f"Supabase message: {message}")


def report_network_error(error):
    print(f"The network request to Supabase failed ({type(error).__name__}).")
    try:
        request_url = error.request.url
    except RuntimeError:
        request_url = None
    host = getattr(request_url, "host", None)
    if host:
        print(f"Supabase host: {host}")
    detail = str(error).strip()
    if detail:
        print(f"Connection detail: {detail}")


def format_currency(value):
    return f"${Decimal(str(value)):.2f}"


def display_table(headers, rows):
    widths = [
        max(len(str(header)), *(len(str(row[index])) for row in rows))
        for index, header in enumerate(headers)
    ]
    row_format = " | ".join(f"{{:<{width}}}" for width in widths)
    print(row_format.format(*headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(row_format.format(*row))


def display_customers(customers):
    print("\nCustomers")
    display_table(
        ["Customer ID", "Customer Name"],
        [[str(row["customer_id"]), row["name"]] for row in customers],
    )


def display_products(products):
    print("\nProducts")
    display_table(
        ["Product ID", "Product Name", "Current Price"],
        [
            [str(row["product_id"]), row["product_name"], format_currency(row["price"])]
            for row in products
        ],
    )


def prompt_for_existing_record(label, records, id_field):
    records_by_id = {int(record[id_field]): record for record in records}
    while True:
        raw_value = input(f"Enter {label} ID: ").strip()
        try:
            record_id = int(raw_value)
        except ValueError:
            print(f"{label} ID must be a whole number. Please try again.")
            continue
        if record_id not in records_by_id:
            print(f"No {label.lower()} with ID {record_id} exists. Please try again.")
            continue
        return records_by_id[record_id]


def prompt_for_quantity():
    while True:
        raw_value = input("Enter quantity: ").strip()
        try:
            quantity = int(raw_value)
        except ValueError:
            print("Quantity must be a positive whole number. Please try again.")
            continue
        if quantity <= 0:
            print("Quantity must be greater than zero. Please try again.")
            continue
        return quantity


def prompt_for_confirmation():
    while True:
        response = input("Confirm this order? (Y/N): ").strip().lower()
        if response in {"y", "n"}:
            return response == "y"
        print("Please enter Y or N.")


def prompt_for_another_order():
    while True:
        response = input("Would you like to enter another order? (Y/N): ").strip().lower()
        if response in {"y", "n"}:
            return response == "y"
        print("Please enter Y or N.")


def get_saved_order(order_id):
    response = (
        get_client()
        .table("orders")
        .select(
            "order_id, customer_id, product_id, quantity, unit_price, order_date, "
            "customers(name), products(product_name)"
        )
        .eq("order_id", order_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def display_saved_order(order):
    customer = order["customers"]
    product = order["products"]
    total = Decimal(str(order["unit_price"])) * int(order["quantity"])
    display_table(
        [
            "Order ID",
            "Customer",
            "Product",
            "Quantity",
            "Unit Price",
            "Total",
            "Order Date",
        ],
        [[
            str(order["order_id"]),
            customer["name"],
            product["product_name"],
            str(order["quantity"]),
            format_currency(order["unit_price"]),
            format_currency(total),
            str(order["order_date"]),
        ]],
    )


def process_order(customers, products):
    customer = prompt_for_existing_record("customer", customers, "customer_id")
    product = prompt_for_existing_record("product", products, "product_id")
    quantity = prompt_for_quantity()

    print("\nOrder summary")
    display_table(
        ["Customer", "Product", "Quantity", "Unit Price", "Order Total"],
        [[
            customer["name"],
            product["product_name"],
            str(quantity),
            format_currency(product["price"]),
            format_currency(Decimal(str(product["price"])) * quantity),
        ]],
    )

    if not prompt_for_confirmation():
        print("Order canceled. No order was inserted.")
        return True

    try:
        inserted_order = create_order(
            customer["customer_id"], product["product_id"], quantity
        )
    except (APIError, httpx.HTTPError, RuntimeError, ValueError):
        print(
            "Supabase did not confirm the order insertion. Check the orders table "
            "before trying again; the program will not retry automatically."
        )
        return False

    order_id = inserted_order.get("order_id")
    if order_id is None:
        print(
            "Supabase did not return the generated order ID. Check the orders table "
            "before trying again; the program will not retry automatically."
        )
        return False

    print(f"\nOrder saved successfully. Order ID: {order_id}")
    try:
        saved_order = get_saved_order(order_id)
    except (APIError, httpx.HTTPError):
        print(
            "Verification could not be completed because the order could not be "
            "retrieved. The order was not inserted again."
        )
        return True

    if saved_order is None:
        print(
            "Verification could not be completed: Supabase returned no matching "
            "order. The order was not inserted again."
        )
        return True

    print("\nVerified order retrieved from Supabase")
    display_saved_order(saved_order)
    return True


def main():
    while True:
        try:
            customers = get_customers()
            products = get_products()
        except ValueError as error:
            print(f"Configuration problem: {error}")
            return
        except APIError as error:
            report_supabase_api_error("read the customer/product tables", error)
            print(
                "Check that the starter SQL ran successfully in this project, the "
                "Data API is enabled, and your .env URL and secret key belong to it."
            )
            return
        except httpx.HTTPError as error:
            report_network_error(error)
            print("Check your internet connection and Supabase project status.")
            return

        if not customers or not products:
            print(
                "No customers or products were found. Run the provided Supabase "
                "starter SQL in your project, then try again."
            )
            return

        display_customers(customers)
        display_products(products)
        if not process_order(customers, products):
            return
        if not prompt_for_another_order():
            print("Goodbye.")
            return


if __name__ == "__main__":
    main()
