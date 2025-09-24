from __future__ import annotations

import sys
from typing import Optional

from tabulate import tabulate
from colorama import Fore, Style, init as colorama_init
from sqlalchemy import select

from .db import SessionLocal, init_db
from .models import Book, Order
from .nlu import parse


class OrderState:
    def __init__(self) -> None:
        self.title: Optional[str] = None
        self.book: Optional[Book] = None
        self.quantity: Optional[int] = None
        self.customer_name: Optional[str] = None
        self.phone: Optional[str] = None
        self.address: Optional[str] = None

    @property
    def done(self) -> bool:
        return all([self.book, self.quantity, self.customer_name, self.phone, self.address])


def find_book_by_title(session, title_like: str) -> Optional[Book]:
    title_like = title_like.strip()
    stmt = select(Book).where(Book.title.ilike(f"%{title_like}%"))
    return session.execute(stmt).scalars().first()


def show_books(session, books) -> None:
    rows = [(b.id, b.title, b.author, float(b.price), b.stock, b.category) for b in books]
    print(tabulate(rows, headers=["ID", "Ten sach", "Tac gia", "Gia", "Ton", "The loai"], tablefmt="github"))


def handle_search(session, intent_name: str, slots: dict) -> None:
    if intent_name == "search_title" and slots.get("title"):
        b = find_book_by_title(session, slots["title"])
        if not b:
            print(Fore.YELLOW + "Khong tim thay sach phu hop." + Style.RESET_ALL)
            return
        show_books(session, [b])
        return

    if intent_name == "search_author" and slots.get("author"):
        stmt = select(Book).where(Book.author.ilike(f"%{slots['author']}%"))
        books = session.execute(stmt).scalars().all()
        if not books:
            print(Fore.YELLOW + "Khong tim thay sach theo tac gia." + Style.RESET_ALL)
            return
        show_books(session, books)
        return

    if intent_name == "search_category" and slots.get("category"):
        stmt = select(Book).where(Book.category.ilike(f"%{slots['category']}%"))
        books = session.execute(stmt).scalars().all()
        if not books:
            print(Fore.YELLOW + "Khong tim thay sach theo the loai." + Style.RESET_ALL)
            return
        show_books(session, books)
        return


def progress_order(session, state: OrderState, user_text: str) -> Optional[str]:
    # Try enrich from NLU first
    intent = parse(user_text)
    if intent.slots.get("title") and not state.book:
        b = find_book_by_title(session, intent.slots["title"])
        if b:
            state.book = b
    if intent.slots.get("quantity") and not state.quantity:
        try:
            state.quantity = int(intent.slots["quantity"])
        except ValueError:
            pass

    # Ask for missing pieces
    if not state.book:
        return "Ban muon mua sach nao? (nhap ten)"
    if not state.quantity:
        return f"Ban muon mua bao nhieu quyen '{state.book.title}'?"
    if state.quantity <= 0:
        state.quantity = None
        return "So luong phai > 0. Ban nhap lai so luong nhe."
    if state.book.stock < state.quantity:
        state.quantity = None
        return f"Chi con {state.book.stock} quyen trong kho. Ban nhap lai so luong nhe."
    if not state.customer_name:
        # Only treat as name when bot explicitly asked for name previously
        if "ho ten" in user_text.lower() or "ten" in user_text.lower():
            pass  # ignore keywords inside name step
        state.customer_name = user_text.strip()
        if len(state.customer_name.split()) < 2:
            state.customer_name = None
            return "Vui long nhap ho ten day du cua ban."
        return "So dien thoai cua ban la?"
    if not state.phone:
        digits = ''.join(ch for ch in user_text if ch.isdigit())
        if len(digits) < 9:
            return "So dien thoai khong hop le. Nhap lai nhe."
        state.phone = digits
        return "Dia chi nhan hang?"
    if not state.address:
        state.address = user_text.strip()

    # All set -> create order
    if state.done:
        order = Order(
            customer_name=state.customer_name or "",
            phone=state.phone or "",
            address=state.address or "",
            book_id=state.book.id,  
            quantity=state.quantity or 1,
            status="confirmed",
        )
        state.book.stock -= state.quantity or 0
        session.add(order)
        session.commit()
        return (
            f"Da dat hang thanh cong: {state.book.title} x{state.quantity}. "
            f"Gui den {state.address}. Ma don: {order.id}. Cam on ban!"
        )

    return None


def run_chat() -> None:
    colorama_init()
    init_db()
    print(Fore.CYAN + "Xin chao! Toi la tro ly cua nha sach. Ban can gi?" + Style.RESET_ALL)
    state: Optional[OrderState] = None

    with SessionLocal() as session:
        while True:
            try:
                user = input(Fore.GREEN + "Ban: " + Style.RESET_ALL)
            except (EOFError, KeyboardInterrupt):
                print("\nTam biet!")
                break

            if not user.strip():
                continue
            if user.lower() in {"thoat", "exit", "quit"}:
                print("Tam biet!")
                break

            if state is not None:
                msg = progress_order(session, state, user)
                if msg:
                    if state.done:
                        print(Fore.CYAN + msg + Style.RESET_ALL)
                        state = None
                    else:
                        print(Fore.CYAN + msg + Style.RESET_ALL)
                continue

            intent = parse(user)
            if intent.name.startswith("search"):
                handle_search(session, intent.name, intent.slots)
                continue
            if intent.name == "order":
                state = OrderState()
                # Pre-fill from parsed slots and ask next question
                msg = progress_order(session, state, user)
                print(Fore.CYAN + (msg or "Toi da ghi nhan yeu cau dat hang.") + Style.RESET_ALL)
                if state.book:
                    print(Fore.CYAN + f"Da tim thay: {state.book.title} (con {state.book.stock})." + Style.RESET_ALL)
                continue

            print(Fore.CYAN + "Toi co the giup tim sach hoac dat sach. Vi du: 'tim Dac Nhan Tam', 'dat sach Nha Gia Kim 2 quyen'." + Style.RESET_ALL)


if __name__ == "__main__":
    run_chat()


