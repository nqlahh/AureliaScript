from models import User, Product
from store_manager import StoreManager

def main():
    # Initialize System
    system = StoreManager()
    
    # Create Sample Data
    admin = User(id=1, username="admin", email="admin@store.com", password_hash="hashed123")
    laptop = Product(id=101, name="Laptop Pro", price=1200.50, stock_quantity=10)
    mouse = Product(id=102, name="Wireless Mouse", price=25.00, stock_quantity=50)
    
    # Populate System
    system.register_customer(admin)
    system.add_product(laptop)
    system.add_product(mouse)
    
    print("System initialized successfully.")

if __name__ == "__main__":
    main()