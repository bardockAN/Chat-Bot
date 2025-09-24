from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(255), index=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(100), index=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="book")

    def __repr__(self) -> str:
        return f"Book(id={self.id}, title={self.title!r}, author={self.author!r})"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(50))
    address: Mapped[str] = mapped_column(String(255))

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    book: Mapped[Book] = relationship(back_populates="orders")

    def __repr__(self) -> str:
        return f"Order(id={self.id}, book_id={self.book_id}, qty={self.quantity})"


