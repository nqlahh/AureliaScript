from dataclasses import dataclass
from enum import Enum

class OrderStatus(Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"

@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str # Simulated hash

@dataclass
class Product:
    id: int
    name: str
    price: float
    stock_quantity: int

@dataclass
class Order:
    id: int
    user_id: int
    items: list[Product] # Composition
    total_amount: float
    status: OrderStatus