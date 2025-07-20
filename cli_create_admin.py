# create_admin.py
from app import app, db
from models.db_template import UserSystem
import getpass


def create_admin():
    print("=== Create Admin User ===")

    # Get user input
    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip()
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    # Validate input
    if not username or not email or not password:
        print("Error: All fields are required")
        return

    if password != confirm_password:
        print("Error: Passwords don't match")
        return

    # Check if username already exists
    with app.app_context():
        if UserSystem.query.filter_by(username=username).first():
            print("Error: Такой логин уже есть")
            return

        if UserSystem.query.filter_by(email=email).first():
            print("Error: Такой Email уже есть")
            return

        try:
            # Create new admin
            admin = UserSystem(username=username, email=email)
            admin.set_password(password)

            # Save to database
            db.session.add(admin)
            db.session.commit()

            # Дебаг в консоль
            print(f"\nAdmin user '{username}' created successfully!")

        except Exception as e:
            print(f"Error creating admin: {str(e)}") # Дебаг в консоль
            db.session.rollback()


if __name__ == "__main__":
    create_admin()