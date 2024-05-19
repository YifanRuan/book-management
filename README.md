# book-management

## Prerequisites

- Postgresql; Tested on postgresql@16

- Python; Tested on python@3.12

- bcrypt

- psycopg2

## Usage

- Create a `book_management` database in psql

- Run `psql book_management -f db_setup.sql`

- In `src`, run `python3 admin.py` to create a super admin account

- Play with `python3 main.py`
