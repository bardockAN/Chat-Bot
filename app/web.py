from __future__ import annotations

from flask import Flask, render_template, request, jsonify
from sqlalchemy import select

from .db import init_db, SessionLocal
from .models import Book, Order
from .nlu import parse


def create_app() -> Flask:
    init_db()
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/message")
    def api_message():
        data = request.get_json(force=True)
        user_text: str = data.get("message", "")
        intent = parse(user_text)

        with SessionLocal() as session:
            if intent.name.startswith("search"):
                if intent.name == "search_title" and (t := intent.slots.get("title")):
                    b = session.execute(select(Book).where(Book.title.ilike(f"%{t}%"))).scalars().first()
                    if not b:
                        return jsonify({"reply": "Khong tim thay sach phu hop."})
                    return jsonify({
                        "reply": f"{b.title} - {b.author} | Gia: {float(b.price)} | Con: {b.stock} | The loai: {b.category}",
                    })
                if intent.name == "search_author" and (a := intent.slots.get("author")):
                    books = session.execute(select(Book).where(Book.author.ilike(f"%{a}%"))).scalars().all()
                    if not books:
                        return jsonify({"reply": "Khong tim thay theo tac gia."})
                    txt = "\n".join(f"- {b.title} ({b.category}) - {float(b.price)}" for b in books[:10])
                    return jsonify({"reply": txt})
                if intent.name == "search_category" and (c := intent.slots.get("category")):
                    books = session.execute(select(Book).where(Book.category.ilike(f"%{c}%"))).scalars().all()
                    if not books:
                        return jsonify({"reply": "Khong tim thay theo the loai."})
                    txt = "\n".join(f"- {b.title} ({b.author}) - {float(b.price)}" for b in books[:10])
                    return jsonify({"reply": txt})

            # quick one-shot order: "dat ... 2 quyen" -> minimal confirmation
            if intent.name == "order" and intent.slots.get("title") and intent.slots.get("quantity"):
                title = intent.slots["title"]
                qty = int(intent.slots["quantity"])
                b = session.execute(select(Book).where(Book.title.ilike(f"%{title}%"))).scalars().first()
                if not b:
                    return jsonify({"reply": "Khong tim thay sach de dat."})
                if b.stock < qty:
                    return jsonify({"reply": f"Chi con {b.stock} quyen."})
                # create placeholder order with dummy info (UI can extend later)
                order = Order(customer_name="Khach Web", phone="000", address="Web", book_id=b.id, quantity=qty, status="web_pending")
                b.stock -= qty
                session.add(order)
                session.commit()
                return jsonify({"reply": f"Da ghi nhan: {b.title} x{qty}. Ma don: {order.id}"})

        return jsonify({"reply": "Toi co the giup tim sach hoac dat sach. Thu: 'tim Dac Nhan Tam'"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


