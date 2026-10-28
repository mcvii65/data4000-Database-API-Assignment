import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

import order_entry
from postgrest.exceptions import APIError


CUSTOMERS = [{"customer_id": 1, "name": "Avery Morgan"}]
PRODUCTS = [{"product_id": 1, "product_name": "Notebook", "price": "4.50"}]


class VerificationQuery:
    def __init__(self, data=None):
        self.data = data if data is not None else [{
            "order_id": 1000,
            "customer_id": 1,
            "product_id": 1,
            "quantity": 2,
            "unit_price": "4.50",
            "order_date": "2026-10-28",
            "customers": {"name": "Avery Morgan"},
            "products": {"product_name": "Notebook"},
        }]

    def select(self, fields):
        self.fields = fields
        return self

    def eq(self, field, value):
        self.filter = (field, value)
        return self

    def limit(self, count):
        self.limit_count = count
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


class VerificationClient:
    def __init__(self, data=None):
        self.query = VerificationQuery(data)

    def table(self, name):
        self.table_name = name
        return self.query


class OrderEntryTests(unittest.TestCase):
    def test_customer_text_and_unknown_id_are_reprompted(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["hello", "999", "1"]):
            with redirect_stdout(output):
                result = order_entry.prompt_for_existing_record(
                    "customer", CUSTOMERS, "customer_id"
                )
        self.assertEqual(result, CUSTOMERS[0])
        self.assertIn("whole number", output.getvalue())
        self.assertIn("No customer with ID 999", output.getvalue())

    def test_unknown_product_id_is_reprompted(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["999", "1"]):
            with redirect_stdout(output):
                result = order_entry.prompt_for_existing_record(
                    "product", PRODUCTS, "product_id"
                )
        self.assertEqual(result, PRODUCTS[0])
        self.assertIn("No product with ID 999", output.getvalue())

    def test_invalid_quantities_are_reprompted(self):
        output = io.StringIO()
        with patch(
            "builtins.input", side_effect=["0", "-2", "1.5", "hello", "3"]
        ):
            with redirect_stdout(output):
                quantity = order_entry.prompt_for_quantity()
        self.assertEqual(quantity, 3)
        self.assertEqual(output.getvalue().count("Please try again"), 4)

    def test_confirmation_reprompts_and_accepts_lowercase(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["maybe", "y"]):
            with redirect_stdout(output):
                confirmed = order_entry.prompt_for_confirmation()
        self.assertTrue(confirmed)
        self.assertIn("Please enter Y or N", output.getvalue())

    def test_cancel_does_not_insert_order(self):
        with patch("builtins.input", side_effect=["1", "1", "2", "n"]):
            with patch("order_entry.create_order") as create_order:
                with redirect_stdout(io.StringIO()):
                    completed = order_entry.process_order(CUSTOMERS, PRODUCTS)
        self.assertTrue(completed)
        create_order.assert_not_called()

    def test_confirmed_order_is_retrieved_with_a_new_query(self):
        client = VerificationClient()
        with patch("builtins.input", side_effect=["1", "1", "2", "Y"]):
            with patch(
                "order_entry.create_order", return_value={"order_id": 1000}
            ) as create_order:
                with patch("order_entry.get_client", return_value=client):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        completed = order_entry.process_order(CUSTOMERS, PRODUCTS)

        self.assertTrue(completed)
        create_order.assert_called_once_with(1, 1, 2)
        self.assertEqual(client.table_name, "orders")
        self.assertEqual(client.query.filter, ("order_id", 1000))
        self.assertIn("Verified order retrieved from Supabase", output.getvalue())
        self.assertIn("$9.00", output.getvalue())

    def test_missing_verification_result_does_not_repeat_insert(self):
        client = VerificationClient(data=[])
        with patch("builtins.input", side_effect=["1", "1", "2", "y"]):
            with patch(
                "order_entry.create_order", return_value={"order_id": 1000}
            ) as create_order:
                with patch("order_entry.get_client", return_value=client):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        completed = order_entry.process_order(CUSTOMERS, PRODUCTS)

        self.assertTrue(completed)
        create_order.assert_called_once_with(1, 1, 2)
        self.assertIn("Verification could not be completed", output.getvalue())
        self.assertNotIn("Verified order retrieved", output.getvalue())

    def test_api_read_error_shows_safe_diagnostic(self):
        error = APIError({
            "code": "PGRST205",
            "message": "Could not find table",
            "details": "sb_secret_this_must_not_appear",
        })
        output = io.StringIO()
        with patch("order_entry.get_customers", side_effect=error):
            with redirect_stdout(output):
                order_entry.main()

        message = output.getvalue()
        self.assertIn("PGRST205", message)
        self.assertIn("Could not find table", message)
        self.assertNotIn("sb_secret_this_must_not_appear", message)
        self.assertIn("starter SQL", message)

    def test_network_error_reports_safe_connection_detail(self):
        error = order_entry.httpx.ConnectError("DNS lookup failed")
        output = io.StringIO()
        with redirect_stdout(output):
            order_entry.report_network_error(error)
        self.assertIn("ConnectError", output.getvalue())
        self.assertIn("DNS lookup failed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
