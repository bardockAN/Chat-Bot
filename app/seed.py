# app/seed.py
from sqlalchemy import select

from .db import SessionLocal, init_db
from .models import Book

SAMPLE_BOOKS = [
    {"title": "Dac Nhan Tam", "author": "Dale Carnegie", "price": 120000, "stock": 15, "category": "Ky nang"},
    {"title": "Nha Gia Kim", "author": "Paulo Coelho", "price": 90000, "stock": 10, "category": "Tieu thuyet"},
    {"title": "Tu duy nhanh va cham", "author": "Daniel Kahneman", "price": 160000, "stock": 8, "category": "Khoa hoc"},
    {"title": "Sach Mat Biec", "author": "Nguyen Nhat Anh", "price": 85000, "stock": 20, "category": "Van hoc"},
    {"title": "Python Co Ban", "author": "Nguyen Van A", "price": 150000, "stock": 25, "category": "CNTT"},
]

def seed() -> None:
    init_db()
    with SessionLocal() as session:
        existing = session.execute(select(Book)).scalars().all()
        if existing:
            # DB đã có dữ liệu thì bỏ qua
            return
        for b in SAMPLE_BOOKS:
            session.add(Book(**b))
        session.commit()

if __name__ == "__main__":
    seed()
