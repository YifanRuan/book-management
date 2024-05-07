import psycopg2
import bcrypt

def connect_db():
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="book_management",
        )
        return connection
    except Exception as e:
        return None
    
def encrypt_password(password):
    encrypted = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return encrypted.decode()

def check_password(password, encrypted_password):
    return bcrypt.checkpw(password.encode(), encrypted_password.encode())

def add_user(connection, username, password, name, sex, age, is_admin=False):
    sex = sex.upper()
    hashed_password = encrypt_password(password)  # 密码加密

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, password, name, sex, age, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (username, hashed_password, name, sex, age, is_admin))
            connection.commit()  # 提交事务
            print("User added successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()  # 如果出错则回滚

def book_search_sql(book_id=None, isbn=None, title=None, author=None, press=None):
    # 构建基本的查询语句
    query = "SELECT id FROM books WHERE "
    conditions = []
    params = []

    # 根据提供的参数动态添加条件
    if book_id:
        conditions.append("books.id = %s")
        params.append(book_id)
    if isbn:
        conditions.append("books.isbn = %s")
        params.append(isbn)
    if title:
        conditions.append("books.title ILIKE %s")
        params.append(f"%{title}%")  # 使用 ILIKE 进行不区分大小写的部分匹配
    if author:
        conditions.append("books.author ILIKE %s")
        params.append(f"%{author}%")
    if press:
        conditions.append("books.press ILIKE %s")
        params.append(f"%{press}%")
    
    # 如果没有提供任何条件，抛出异常或返回所有书籍
    if not conditions:
        print("No search criteria provided. Will search on all books.")
        query = "SELECT id FROM books;"
    else:
        query += ' AND '.join(conditions)
        query += ";"

    return query, params

def basic_book_search(connection, book_id=None, isbn=None, title=None, author=None, press=None):
    # 构建基本的查询语句
    query = "SELECT * FROM books WHERE "
    conditions = []
    params = []

    # 根据提供的参数动态添加条件
    if book_id:
        conditions.append("books.id = %s")
        params.append(book_id)
    if isbn:
        conditions.append("books.isbn = %s")
        params.append(isbn)
    if title:
        conditions.append("books.title ILIKE %s")
        params.append(f"%{title}%")  # 使用 ILIKE 进行不区分大小写的部分匹配
    if author:
        conditions.append("books.author ILIKE %s")
        params.append(f"%{author}%")
    if press:
        conditions.append("books.press ILIKE %s")
        params.append(f"%{press}%")
    
    # 如果没有提供任何条件，抛出异常或返回所有书籍
    if not conditions:
        print("No search criteria provided. Will search on all books.")
        query = "SELECT * FROM books ORDER BY id;"
    else:
        query += ' AND '.join(conditions)
        query += " ORDER BY id;"

    # 执行查询
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    
def update_book_info(connection, book_id, title=None, author=None, press=None, sale_price=None):
    query = "UPDATE books SET"
    updates = []
    params = []
    
    if title:
        updates.append(" title = %s")
        params.append(title)
    if author:
        updates.append(" author = %s")
        params.append(author)
    if press:
        updates.append(" press = %s")
        params.append(press)
    if sale_price is not None:  # 允许将价格更新为0或NULL
        updates.append(" sale_price = %s")
        params.append(sale_price)
    
    # 如果没有提供更新内容，则不执行操作
    if not updates:
        print("No updates provided.")
        return
    
    # 将更新的字段合并到查询语句中，并添加WHERE子句
    query += ",".join(updates) + " WHERE id = %s;"
    params.append(book_id)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()  # 确保提交更改
            print("Book information updated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        connection.rollback()
