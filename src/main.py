import getpass
from helper import connect_db, check_password, add_user, book_search_sql, basic_book_search, update_book_info

def main():
    connection = connect_db()
    if not connection:
        print("Failed to connect to database.")
        return
    print("Connected to database.")
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    successful, su = login(connection, username, password)
    if not successful:
        print("Login failed!")
        return
    print("Login successful!")
    while True:
        print("")
        if su:
            print("You are admin user.")
        print("Please choose an option:")
        print("1. Search books")
        print("2. Modify books")
        print("3. Import books")
        print("4. Search imported books")
        print("5. Pay for imported books")
        print("6. Return imported books")
        print("7. Add new books")
        print("8. Buy books")
        print("9. Check statement")
        print("q. Logout")
        if su:
            print("a. Add user")
            print("b. List user")
        option = input("Enter option: ").lower()
        if option == "1":
            search_books(connection)
        elif option == "2":
            modify_books(connection)
        elif option == "3":
            import_books(connection)
        elif option == "4":
            search_imported_books(connection)
        elif option == "5":
            pay_for_imported_books(connection)
        elif option == "6":
            return_imported_books(connection)
        elif option == "7":
            add_new_books(connection)
        elif option == "8":
            buy_books(connection)
        elif option == "9":
            check_statement(connection)
        elif option == "q":
            break
        elif su:
            if option == "a":
                add_normal_user(connection)
            elif option == "b":
                list_user(connection)
            else:
                print("Invalid option!")
        else:
            print("Invalid option!")
    connection.close()
    print("GoodBye!")

# user: username, password, name, id, sex, age, is_admin
def login(connection, username, password):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        user = cursor.fetchone()
        if user and check_password(password, user[2]):
            user_id = user[0]
            cursor.execute("SET myapp.user_id = %s", (user_id,))
            print(f"User ID set to {user_id} for this session.")
            print("Hello,", user[1])
            return True, user[6]
        return False, False

def search_books(connection):
    try:
        book_id = int(input("Enter book id: "))
    except ValueError:
        print("Invalid book id. Will not use book id to search.")
        book_id = None
    isbn = input("Enter book isbn: ").strip()
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    press = input("Enter book press: ").strip()
    # 过滤掉空字符串，只传递有输入的参数
    results = basic_book_search(connection, 
                                book_id=book_id,
                                isbn=isbn if isbn else None, 
                                title=title if title else None, 
                                author=author if author else None, 
                                press=press if press else None)
    if not results:
        print("No results found!")
        return
    print("Books: [id, isbn, title, author, press, quantity, sale_price]")
    for result in results:
        print(result)


def modify_books(connection):
    try:
        book_id = int(input("Enter book id: "))
    except ValueError:
        print("Invalid book id.")
        return
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    press = input("Enter book press: ").strip()
    try:
        new_price = float(input("Enter new price: "))
    except ValueError:
        print("Invalid price. Will not update price.")
        new_price = None
    update_book_info(connection,
                        book_id=book_id,
                        title=title if title else None,
                        author=author if author else None,
                        press=press if press else None,
                        sale_price=new_price)


def import_books(connection):
    isbn = input("Enter book isbn: ").strip()
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    press = input("Enter book press: ").strip()
    results = basic_book_search(connection, 
                                book_id=None,
                                isbn=isbn if isbn else None, 
                                title=title if title else None, 
                                author=author if author else None, 
                                press=press if press else None)
    if results:
        if len(results) > 1:
            print("Multiple books found. Please choose one:")
            cnt = 0
            for result in results:
                print(cnt, result)
                cnt += 1
            try:
                choice = int(input("Enter choice: "))
            except ValueError:
                print("Invalid choice")
                return
            if choice < 0 or choice >= cnt:
                print("Invalid choice")
                return
            book_id = results[choice][0]
        else:
            print("Book found.")
            book_id = results[0][0]
    else:
        print("No book found. Will add new book.")
        isbn = input("Enter book isbn: ").strip() if not isbn else isbn
        title = input("Enter book title: ").strip() if not title else title
        author = input("Enter book author: ").strip() if not author else author
        press = input("Enter book press: ").strip() if not press else press
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO books (isbn, title, author, press, quantity)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (isbn, title, author, press, 0))
                book_id = cursor.fetchone()[0]
                connection.commit()
                print("New book added with ID:", book_id)
        except Exception as e:
            connection.rollback()
            print("An error occurred:", e)
            return
    
    try:
        cost_price = float(input("Enter cost price: "))
        quantity = int(input("Enter quantity: "))
    except ValueError:
        print("Invalid input")
        return
    if (cost_price < 0 or quantity < 0):
        print("Invalid input")
        return
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO imports (book_id, cost_price, quantity)
                VALUES (%s, %s, %s);
            """, (book_id, cost_price, quantity))
            connection.commit()
            print("Books imported successfully.")
    except Exception as e:
        connection.rollback()
        print("An error occurred:", e)


def search_imported_books(connection):
    try:
        book_id = int(input("Enter book id: "))
    except ValueError:
        print("Invalid book id. Will not use book id to search.")
        book_id = None
    isbn = input("Enter book isbn: ").strip()
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    press = input("Enter book press: ").strip()
    query, params = book_search_sql(book_id, isbn, title, author, press)
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT * FROM imports WHERE book_id in ({query.strip(';')});
        """, params)
        results = cursor.fetchall()
        if not results:
            print("No results found.")
            return
        print("Imports: [id, book_id, cost_price, quantity, is_paid]")
        for result in results:
            print(result)

def pay_for_imported_books(connection):
    try:
        id = int(input("Enter import id: "))
    except ValueError:
        print("Invalid import id. Will not use import id to search.")
        id = None
    
    if id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE imports
                    SET is_paid = TRUE
                    WHERE id = %s AND is_paid = FALSE;
                """, (id,))
                connection.commit()
                print("Books are paid.")
        except Exception as e:
            connection.rollback()
            print("An error occurred:", e)
        return

    try:
        book_id = int(input("Enter book id: "))
    except ValueError:
        print("Invalid book id. Will not use book id to search.")
        book_id = None
    isbn = input("Enter book isbn: ").strip()
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    press = input("Enter book press: ").strip()
    query, params = book_search_sql(book_id, isbn, title, author, press)

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                Update imports
                SET is_paid = TRUE
                WHERE book_id in ({query.strip(';')}) AND is_paid = FALSE;
            """, params)

            # 提交事务
            connection.commit()
            print("Books are paid.")

    except Exception as e:
        # 如果出现错误，则回滚事务
        connection.rollback()
        print("An error occurred:", e)


def return_imported_books(connection):
    try:
        id = int(input("Enter import id: "))
    except ValueError:
        print("Invalid import id. Will not use import id to search.")
        id = None
    
    if id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM imports
                    WHERE id = %s AND is_paid = FALSE;
                """, (id,))
                connection.commit()
                print("Books are returned.")
        except Exception as e:
            connection.rollback()
            print("An error occurred:", e)
        return
    
    try:
        book_id = int(input("Enter book id: "))
    except ValueError:
        print("Invalid book id. Will not use book id to search.")
        book_id = None
    isbn = input("Enter book isbn: ").strip()
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    press = input("Enter book press: ").strip()
    query, params = book_search_sql(book_id, isbn, title, author, press)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                DELETE FROM imports
                WHERE book_id in ({query.strip(';')}) AND is_paid = FALSE;
            """, params)
            
            # 提交事务
            connection.commit()
            print("Books are returned.")

    except Exception as e:
        # 如果出现错误，则回滚事务
        connection.rollback()
        print("An error occurred:", e)
    

def add_new_books(connection):
    try:
        id = int(input("Enter import id: "))
    except ValueError:
        print("Invalid import id. Will not use import id to search.")
        id = None
    
    if id:
        try:
            sale_price = float(input("Enter sale price: "))
        except ValueError:
            print("Invalid sale price.")
            return
        try:
            with connection.cursor() as cursor:
                # 首先更新 books 表的库存
                cursor.execute("""
                    UPDATE books
                    SET quantity = quantity + COALESCE((
                            SELECT SUM(quantity)
                            FROM imports
                            WHERE id = %s AND is_paid = TRUE
                        ), 0),  -- 如果没有记录，则加 0
                        sale_price = %s  -- 更新销售价格
                    WHERE id in (SELECT book_id FROM imports WHERE id = %s);
                """, (id, sale_price, id))
                
                # 接着删除已支付的 imports 记录
                cursor.execute("""
                    DELETE FROM imports
                    WHERE id = %s AND is_paid = TRUE;
                """, (id,))
                
                # 提交事务
                connection.commit()
                print("Added new books!")

        except Exception as e:
            # 如果出现错误，则回滚事务
            connection.rollback()
            print("An error occurred:", e)
        return
    
    try:
        book_id = int(input("Enter book id: "))
    except ValueError:
        print("Invalid book id. Will not use book id to search.")
        book_id = None
    isbn = input("Enter book isbn: ").strip()
    title = input("Enter book title: ").strip()
    author = input("Enter book author: ").strip()
    press = input("Enter book press: ").strip()
    query, params = book_search_sql(book_id, isbn, title, author, press)
    try:
        sale_price = float(input("Enter sale price: "))
    except ValueError:
        print("Invalid sale price.")
        return
    
    try:
        with connection.cursor() as cursor:
            # 首先更新 books 表的库存
            cursor.execute(f"""
                UPDATE books
                SET quantity = quantity + COALESCE((
                        SELECT SUM(quantity)
                        FROM imports
                        WHERE book_id in {query.strip(';')} AND is_paid = TRUE
                    ), 0),  -- 如果没有记录，则加 0
                    sale_price = %s  -- 更新销售价格
                WHERE id in {query.strip(';')};
            """, params + [sale_price] + params)
            
            # 接着删除已支付的 imports 记录
            cursor.execute(f"""
                DELETE FROM imports
                WHERE book_id in {query.strip(';')} AND is_paid = TRUE;
            """, params)
            
            # 提交事务
            connection.commit()
            print("Added new books!")

    except Exception as e:
        # 如果出现错误，则回滚事务
        connection.rollback()
        print("An error occurred:", e)


def buy_books(connection):
    try:
        book_id = int(input("Enter book id: "))
        quantity = int(input("Enter quantity: "))
    except ValueError:
        print("Invalid number.")
        return
    if quantity <= 0:
        print("Quantity must be positive!")
        return
    try:
        with connection.cursor() as cursor:
            # SQL 语句使用 WITH 语句检查并更新库存
            cursor.execute("""
                WITH checked_books AS (
                    SELECT id FROM books
                    WHERE id = %s AND quantity >= %s
                    FOR UPDATE
                )
                UPDATE books
                SET quantity = quantity - %s
                WHERE id IN (SELECT id FROM checked_books)
                RETURNING id;
            """, (book_id, quantity, quantity))

            updated_book = cursor.fetchone()
            if updated_book is None:
                connection.rollback()  # 保证如果没有足够库存，则撤销所有更改
                print("Not enough stock available or book does not exist.")
            else:
                connection.commit()
                print("Purchase successful. Book quantity updated.")
    except Exception as e:
        connection.rollback()
        print("An error occurred:", e)

def check_statement(connection):
    start_time = input("Input start time in format yyyy-mm-dd: ").strip()
    if not start_time:
        start_time = "1970-01-01"
    end_time = input("Input end time in format yyyy-mm-dd: ").strip()
    if not end_time:
        end_time = "9999-12-31"
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM transactions
            WHERE transaction_time >= %s AND transaction_time <= %s;
        """, (start_time, end_time))
        transactions = cursor.fetchall()
        if not transactions:
            print("No transactions found.")
            return
        print("Transactions: [id, user_id, book_id, time, quantity, balance_change]")
        for transaction in transactions: 
            print(transaction)

def add_normal_user(connection):
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    name = input("Enter name: ")
    sex = input("Enter sex(M/F/O): ")
    try:
        age = int(input("Enter age: "))
    except ValueError:
        print("Invalid age.")
        return
    add_user(connection, username, password, name, sex, age)

def list_user(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print("Users: [id, username, name, sex, age, is_admin]")
        for user in users:
            print(user[:2] + user[3:])

if __name__ == "__main__":
    main()
