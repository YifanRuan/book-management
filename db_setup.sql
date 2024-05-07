DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    id SERIAL PRIMARY KEY,                -- 使用 SERIAL 自增主键
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    sex CHAR(1) CHECK (sex IN ('M', 'F', 'O')),
    age INTEGER CHECK (age >= 0),
    is_admin BOOLEAN DEFAULT FALSE
);

DROP TABLE IF EXISTS books CASCADE;
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    press VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),  -- 确保数量非负
    sale_price NUMERIC(10, 2) CHECK (sale_price >= 0)  -- 允许销售价格为 NULL
);

DROP TABLE IF EXISTS imports CASCADE;
CREATE TABLE imports (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    cost_price NUMERIC(10, 2) NOT NULL CHECK (cost_price >= 0),  -- 使用 cost_price 代替 purchase_price，确保成本价非负
    quantity INTEGER NOT NULL CHECK (quantity >= 0),  -- 确保数量非负
    is_paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

DROP TABLE IF EXISTS transactions CASCADE;
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    transaction_time TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),  -- 自动记录交易时间
    quantity INTEGER NOT NULL CHECK (quantity > 0),  -- 交易数量必须为正
    balance_change NUMERIC(10, 2) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),  -- 假设已有 users 表
    FOREIGN KEY (book_id) REFERENCES books(id)  -- 假设已有 books 表
);

CREATE OR REPLACE FUNCTION fn_book_sale()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id INTEGER;
BEGIN
    SELECT current_setting('myapp.user_id') INTO current_user_id;
    INSERT INTO transactions (user_id, book_id, transaction_time, quantity, balance_change)
    VALUES (current_user_id, NEW.id, NOW(), OLD.quantity - NEW.quantity, (OLD.quantity - NEW.quantity) * NEW.sale_price);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_book_sale ON books;
CREATE TRIGGER trg_book_sale
AFTER UPDATE OF quantity ON books
FOR EACH ROW
WHEN (OLD.quantity > NEW.quantity)
EXECUTE PROCEDURE fn_book_sale();

CREATE OR REPLACE FUNCTION fn_book_import()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id INTEGER;
BEGIN
    -- 获取当前设置的用户 ID
    current_user_id := current_setting('myapp.user_id')::INTEGER;
    INSERT INTO transactions (user_id, book_id, transaction_time, quantity, balance_change)
    VALUES (current_user_id, NEW.book_id, NOW(), NEW.quantity, -NEW.quantity * NEW.cost_price);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_book_import ON imports;
CREATE TRIGGER trg_book_import
AFTER UPDATE OF is_paid ON imports
FOR EACH ROW
WHEN (OLD.is_paid IS FALSE AND NEW.is_paid IS TRUE)
EXECUTE PROCEDURE fn_book_import();
