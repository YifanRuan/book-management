import getpass
from helper import connect_db, add_user

def main():
    connection = connect_db()
    if not connection:
        print("Failed to connect to database")
        return
    print("Connected to database")
    add_admin(connection)
    connection.close()

def add_admin(connection):
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    name = input("Enter your name: ")
    sex = input("Enter your sex(M/F/O): ")
    age = int(input("Enter your age: "))
    is_admin = True
    add_user(connection, username, password, name, sex, age, is_admin)

if __name__ == "__main__":
    main()
