from __future__ import annotations

import streamlit as st
from sqlalchemy import select

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db import init_db, SessionLocal
from app.models import Book, Order
from app.nlu import parse


st.set_page_config(page_title="Bookstore Chatbot", page_icon="📚", layout="centered")

@st.cache_resource
def _init():
    init_db()
    return True

_init()

st.title("📚 Bookstore Chatbot")
st.caption("Tim sach · Dat hang (demo Streamlit)")

if "history" not in st.session_state:
    st.session_state.history = [("bot", "Xin chao! Toi co the giup tim sach hoac dat sach.")]
if "order_state" not in st.session_state:
    st.session_state.order_state = {}

def show_message(role: str, text: str):
    with st.chat_message("assistant" if role == "bot" else "user"):
        st.markdown(text)

for role, text in st.session_state.history:
    show_message(role, text)

def handle_message(user_text: str):
    intent = parse(user_text)
    with SessionLocal() as session:
        if intent.name.startswith("search"):
            if intent.name == "search_title" and (t := intent.slots.get("title")):
                b = session.execute(select(Book).where(Book.title.ilike(f"%{t}%"))).scalars().first()
                if not b:
                    reply = "Khong tim thay sach phu hop."
                else:
                    reply = f"**{b.title}** — {b.author}\n\nGia: {float(b.price)} | Con: {b.stock} | The loai: {b.category}"
                st.session_state.history.append(("user", user_text))
                st.session_state.history.append(("bot", reply))
                return
            if intent.name == "search_author" and (a := intent.slots.get("author")):
                books = session.execute(select(Book).where(Book.author.ilike(f"%{a}%"))).scalars().all()
                if not books:
                    reply = "Khong tim thay theo tac gia."
                else:
                    reply = "\n".join([f"- **{b.title}** ({b.category}) — {float(b.price)}" for b in books[:15]])
                st.session_state.history.append(("user", user_text))
                st.session_state.history.append(("bot", reply))
                return
            if intent.name == "search_category" and (c := intent.slots.get("category")):
                books = session.execute(select(Book).where(Book.category.ilike(f"%{c}%"))).scalars().all()
                if not books:
                    reply = "Khong tim thay theo the loai."
                else:
                    reply = "\n".join([f"- **{b.title}** ({b.author}) — {float(b.price)}" for b in books[:15]])
                st.session_state.history.append(("user", user_text))
                st.session_state.history.append(("bot", reply))
                return

        if intent.name == "order":
            title = intent.slots.get("title")
            qty = int(intent.slots.get("quantity", 1))
            if not title:
                st.session_state.history.append(("user", user_text))
                st.session_state.history.append(("bot", "Ban muon mua sach nao?"))
                return
            b = session.execute(select(Book).where(Book.title.ilike(f"%{title}%"))).scalars().first()
            if not b:
                st.session_state.history.append(("user", user_text))
                st.session_state.history.append(("bot", "Khong tim thay sach de dat."))
                return
            if b.stock < qty:
                st.session_state.history.append(("user", user_text))
                st.session_state.history.append(("bot", f"Chi con {b.stock} quyen trong kho."))
                return
            order = Order(customer_name="Khach Streamlit", phone="000", address="Web", book_id=b.id, quantity=qty, status="web_pending")
            b.stock -= qty
            session.add(order)
            session.commit()
            st.session_state.history.append(("user", user_text))
            st.session_state.history.append(("bot", f"Da ghi nhan: {b.title} x{qty}. Ma don: {order.id}"))
            return

        st.session_state.history.append(("user", user_text))
        st.session_state.history.append(("bot", "Toi co the giup tim sach hoac dat sach. Thu: 'tim Dac Nhan Tam'"))


if prompt := st.chat_input("Nhap tin nhan..."):
    handle_message(prompt)
    show_message("user", prompt)
    show_message("bot", st.session_state.history[-1][1])


