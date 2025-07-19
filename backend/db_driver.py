import sqlite3
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager

@dataclass
class Car:
    name: str
    email: str
    interest: str

class DatabaseDriver:
    def __init__(self, db_path: str = "customer_db.sqlite"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create cars table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer (
                    name TEXT NOT NULL,
                    email TEXT PRIMARY KEY,
                    interest TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_car(self, name: str, email: str, interest: str) -> Car:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customer (name, email, interest) VALUES (?, ?, ?)",
                (name, email, interest)
            )
            conn.commit()
            return Car(name=name, email=email, interest=interest)

    def get_car_by_email(self, email: str) -> Optional[Car]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cars WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return Car(
                name=row[0],
                email=row[1],
                interest=row[2],
            )
