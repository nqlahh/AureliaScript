import threading

class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.connected = False
        self.users = []
        self.products = []

    def connect(self):
        if not self.connected:
            print("Connecting to Database...")
            self.connected = True
            print("Database Connected.")
        
    def get_connection(self):
        if not self.connected:
            self.connect()
        return self