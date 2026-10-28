# DATA 4000 — Python + Supabase API Lab
Fairfield University · Illya Mowerman, Ph.D.

## DATA 4000 order-entry assignment

The required terminal program is `order_entry.py`. It reads customers and products
from Supabase, validates each entry, asks for confirmation, inserts one order,
then makes a separate Supabase query to retrieve and display the saved order.
It does not use the CSV files for the catalog display and does not start a web app.

### Setup and run

1. Create your own Supabase project. In its SQL Editor, run the complete
   `DATA_4000_Supabase_Starter.sql` file provided for this assignment once. It
   creates and seeds the `customers`, `products`, and `orders` tables. Use a new,
   otherwise-empty project; do not run it if those tables already exist.
2. In the VS Code terminal at the repository root, install the dependencies and
   create `.env` from `.env.example` if you do not already have `.env`:

   macOS / Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install -r requirements.txt
   cp -n .env.example .env
   ```

   Windows PowerShell:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

3. In your local `.env`, replace the placeholders with your own Supabase project
   URL and secret API key if you have not configured it already. Keep an existing
   `.env` file rather than overwriting it. Never commit or share `.env`;
   `.gitignore` excludes it.
4. Run the required command in the VS Code terminal:
   ```bash
   python order_entry.py
   ```

Follow the prompts to choose existing IDs, enter a positive whole-number quantity,
and confirm with Y or N. On confirmation, the program gets the current price from
the product table, lets Supabase generate the order ID, and queries that ID again
to verify the saved record. If verification fails, it reports that and does not
repeat the insert. After a successful order or cancellation, it offers to start
another order.

### Assignment test results

Run the local tests with:
```bash
python -m unittest discover -s tests -v
```

Result on October 28, 2026: **PASS — 9 tests passed.** The tests exercise text and
unknown IDs, all required invalid quantities (`0`, `-2`, `1.5`, and `hello`),
confirmation reprompting, cancellation without an insert, a confirmed order
followed by a separate verification query, and no retry when verification
returns no order. They also cover safe diagnostics for API and network errors.
These tests use mocked Supabase responses and do not change the hosted database.

Live connectivity/cancellation check on October 28, 2026: **PASS** — the program
loaded 20 customers and 12 products from Supabase and canceled at confirmation;
no insert was attempted during that cancellation check.

Live saved-order verification on October 28, 2026: **PASS** — the `orders` table
contained order ID 1001, above the 60 seeded orders. A fresh Supabase API query
filtered to order ID 1001 returned the saved record below. This check did not
insert another order. The displayed total is quantity multiplied by the
retrieved stored unit price. The order was already present when this verification
was run, so this output documents the persisted row and separate retrieval rather
than the original insert response.

Copied terminal output from the fresh verification query:
```text
Fresh Supabase verification query returned:
Order ID | Customer     | Product   | Quantity | Unit Price | Total   | Order Date
---------+--------------+-----------+----------+------------+---------+-----------
1001     | Riley Brooks | Desk Lamp | 10       | $29.00     | $290.00 | 2026-10-28
```
Enter customer ID: mike
customer ID must be a whole number. Please try again.

Enter customer ID: 1000000000000000
No customer with ID 1000000000000000 exists. Please try again.

Enter product ID: 100000000000
No product with ID 100000000000 exists. Please try again.

Enter product ID: -2
No product with ID -2 exists. Please try again.

Order summary
Customer     | Product  | Quantity | Unit Price | Order Total
-------------+----------+----------+------------+------------
Jordan Patel | Backpack | 2        | $45.00     | $90.00
Confirm this order? (Y/N): N
Order canceled. No order was inserted.

Verified order retrieved from Supabase
Order ID | Customer     | Product  | Quantity | Unit Price | Total | Order Date
---------+--------------+----------+----------+------------+-------+-----------
1002     | Avery Morgan | Notebook | 1        | $4.50      | $4.50 | 2026-10-28

## Broader Supabase API lab (separate workflow)

The remaining sections describe the broader CSV/import lab, which uses
`sql/01_create_tables.sql` and Python data loaders. For the order-entry assignment,
follow the setup above and run the complete provided `DATA_4000_Supabase_Starter.sql`
instead. Do not combine both database setup paths in one Supabase project.

## CSV lab: setup and workflow
Build a fictional campus store database, upload CSV records with Python, and use
an API to read and change records. Plan for 75–90 minutes with accounts created
before class. Python fundamentals (functions, lists, dictionaries, imports) are assumed.
Use Python 3.11 or newer and VS Code. No actual customer data is used.

## What is happening?
Python reads CSV text into dictionaries. The Supabase Python library sends those
dictionaries as JSON over HTTPS to Supabase's Data API. The API reads/writes
PostgreSQL tables and sends JSON back. `.execute()` triggers a request; `.data`
contains the returned Python records. This lab does NOT use a PostgreSQL connection
string, database password, or Django ORM.

CSV → Python → HTTPS Data API → Supabase PostgreSQL.
Later: Streamlit widget or Django view → the same Python functions → Data API.

## Files and order
| File | Purpose |
|---|---|
| data/customers.csv | 20 fictional customers |
| data/products.csv | 12 products |
| data/orders.csv | 60 one-product orders |
| sql/01_create_tables.sql | Tables, constraints, and restricted access |
| config.py | Read local configuration |
| database.py | Reusable API functions |
| 01_check_connection.py | Check access before uploading |
| 02_import_data.py | Validate and upload CSV records |
| 03_query_data.py | Read, filter, join, calculate revenue |
| 04_modify_data.py | Insert, update, delete demonstration |
| 05_raw_api.py | Optional HTTP request without the client library |
| app_streamlit.py | Optional local application bridge |
| exercises.py / solutions.py | Student practice and worked answers |
| EXPECTED_RESULTS.md | Baseline results for verification |
| INSTRUCTOR_GUIDE.md | Lesson flow and discussion prompts |

## 1. Create your own Supabase project
Create a dedicated classroom project at https://supabase.com/dashboard and wait
for it to finish provisioning. Each student should use their own project. Do not
share the instructor's administrative credentials with students.
Open SQL Editor, paste sql/01_create_tables.sql, and run it once.
The script creates public.customers, public.products, and public.orders.
Check Table Editor: all three tables should exist and initially be empty.
If you already have tables with these names, use a new project; this script does
not overwrite them. SQL defines the structure; the later Python script loads data.
Ensure the Data API is enabled and the public schema is exposed in project API settings.

## 2. Open the extracted folder in VS Code
Open the whole supabase_class folder, then open its terminal.
Create a virtual environment:

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```
Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```
If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` in place
of `python` for installation and scripts; activation is not essential.
In VS Code use Python: Select Interpreter and choose the .venv interpreter.
Dependencies use compatible major-version ranges, not a fully locked environment.

## 3. Set configuration
In Supabase, find your project URL in the Connect dialog and a secret API key in
Settings → API Keys. Create a secret key if needed. Edit the local .env file:
```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=sb_secret_your_actual_key
```
Use the project API URL, not the browser dashboard address. The secret key is not
the database password. This kit expects the current sb_secret_ key format.

This is a private, local administrative exercise: each person uses their own
secret key. Row Level Security is enabled, with no public access policies, and
anon/authenticated table privileges are revoked. The secret key uses service_role,
which bypasses RLS. A publishable key therefore cannot substitute for this key.
Never put .env in GitHub, slides, screenshots, AI prompts, or student submissions.
The included .gitignore excludes it. If exposed, rotate the key in Supabase.

## 4. Validate, connect, and upload
```bash
python 02_import_data.py --check-only
python 01_check_connection.py
python 02_import_data.py
python 01_check_connection.py
```
The offline check does not need packages or credentials. Expect 20 customers,
12 products, and 60 orders. The connection check reports 0 products before import
and 12 afterward. Refresh Table Editor to see the records.
The loader converts CSV strings to integers where required and validates keys,
quantities, dates, and prices before calling the API. Prices are sent as decimal
strings and stored as PostgreSQL numeric values.

Customers and products must load before orders because orders contain foreign keys.
The loader uses upsert: an existing primary key is updated, otherwise inserted.
Re-running restores the seeded values, including catalog prices. It does not remove
extra records created during exercises. Uploads are three separate requests, not
one all-or-nothing transaction. If a request fails, fix the issue and rerun.

## 5. Query and modify
```bash
python 03_query_data.py
python 04_modify_data.py
python 05_raw_api.py
```
Read database.py beside each example. The modify script requires typing YES,
adds one fictional demo customer, changes a product price, creates/deletes one
order, and restores the product price in a finally block. An abrupt process stop
can leave partial changes: inspect the tables and rerun the importer to restore
seed prices. Additional demo customers are intentionally retained.
Use an equality filter for every targeted update/delete. A foreign key prevents
an order from referring to a nonexistent customer or product.

The raw HTTP example returns status 200 and a JSON list. Its apikey request header
identifies the calling component. The library normally handles HTTP details for us.

## 6. Practice
Read exercises.py, complete the TODOs, and run:
```bash
python exercises.py
```
Use solutions.py after attempting the exercises. Run baseline comparisons before
adding orders. See EXPECTED_RESULTS.md.

## 7. Optional Streamlit bridge
```bash
python -m pip install -r requirements-app.txt
python -m streamlit run app_streamlit.py --server.address 127.0.0.1
```
Open the local address printed in the terminal. The app shows the product catalog,
records purchases, and reads saved orders using database.py. Every successful
submission creates a new order. This is an unauthenticated LOCAL admin demo;
do not publish it as-is. Server-held credentials do not by themselves authorize
visitors to change data. Before public deployment add user authentication and
per-user authorization, with appropriately scoped RLS policies and user sessions,
or a carefully authorized backend. Store deployment secrets in the hosting
platform's secret manager.

For Django, a view can import `get_products` or `create_order` from database.py.
A POST form needs Django CSRF protection, input validation, authentication, and
authorization before calling write functions. Using this API approach is different
from configuring Django's PostgreSQL ORM. A full Django project is a later lesson.

## Data dictionary and design
| Table | Column | Type / meaning |
|---|---|---|
| customers | customer_id | Integer primary key |
| customers | name, email, city | Text; email is unique |
| products | product_id | Integer primary key |
| products | product_name, category | Text |
| products | price | Current catalog price, dollars, 2 decimals |
| orders | order_id | Integer primary key |
| orders | customer_id, product_id | Foreign keys to the parent tables |
| orders | quantity | Positive integer |
| orders | order_date | ISO date YYYY-MM-DD |
| orders | unit_price | Price per unit at purchase time |

One customer can have many orders; one product can appear in many orders.
Each order contains ONE product, possibly multiple units. A full shopping cart
would usually separate orders from order_items, adding a fourth table.
Seed IDs are below 1000; generated IDs start at 1000 to avoid sequence collisions
when new rows are inserted. All names are fictional and emails use example.com.
The data is fixed, reproducible, and dated September 2026.

## Scope of the teaching example
The read functions use one API response. Supabase commonly limits responses to
1000 records; use pagination for larger datasets. Revenue is labeled as the total
of returned rows. Recording an order reads a product price and then inserts the
order in separate requests. A production checkout should enforce authoritative
pricing, inventory, and atomicity in a database function/transaction. This lesson
has no payments, inventory, taxes, shipping, or production checkout guarantees.

## Troubleshooting
| Symptom | What to check |
|---|---|
| ModuleNotFoundError | Install requirements with the same Python interpreter running the script. |
| Configuration ValueError | .env must sit beside config.py; replace both placeholders. Existing shell environment variables take precedence. |
| HTTP 401 / invalid API key | URL and secret key must belong to the same project; check key status. |
| Permission denied / empty public reads | Use your own secret key for this lab; public access is intentionally restricted. |
| Table not found / schema cache | Run SQL first, confirm public schema is exposed, then retry after the schema cache refreshes. |
| Foreign-key error | Upload parents first; customer/product IDs must exist. |
| Unique email error | Choose a new fictional email or inspect the existing customer. |
| Relation already exists | Setup SQL was already run; skip it or use a new project. |
| Counts exceed baseline | Demo customers or app orders remain; seed upsert does not delete them. |
| Network / project unavailable | Check internet access and that the Supabase project is running. |

## Reference documentation
API syntax and key guidance checked October 14, 2026:
- https://supabase.com/docs/reference/python/initializing
- https://supabase.com/docs/reference/python/select
- https://supabase.com/docs/reference/python/insert
- https://supabase.com/docs/reference/python/upsert
- https://supabase.com/docs/guides/getting-started/api-keys

Validation: CSV relationships and totals and Python syntax checked locally.
A live Supabase round-trip requires your project and credentials and was not run
when this kit was created. Run the connection/import checks before class.
