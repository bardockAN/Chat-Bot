# streamlit_app.py
import os, sys, unicodedata, difflib, re
from dotenv import load_dotenv
import streamlit as st

# Cho phép import gói "app.*"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# ======= MODE =======
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes", "y")
if DEMO_MODE:
    # Tránh circular import: import và gọi trong try
    try:
        from app.seed import seed as run_seed
        run_seed()
    except Exception:
        pass

USE_LLM = False  # tắt mặc định để tránh phụ thuộc API key

# ==================== UI CONFIG ====================
st.set_page_config(page_title="BookStore Chatbot", page_icon="📚", layout="wide")
st.title("📚 BookStore Chatbot")
st.caption(f"Exact + Fuzzy + ID/Author/Category + Admin • DEMO_MODE={DEMO_MODE}")

# ---------------- HELPERS ----------------
def strip_accents(s: str) -> str:
    s = unicodedata.normalize('NFD', s or "")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

def norm_key(s: str) -> str:
    return strip_accents(s).strip().lower()

def fmt_price(v) -> str:
    try:
        return f"{float(v):,.0f}đ"
    except Exception:
        return f"{v}đ"

def fuzzy_suggest(query: str, titles: list[str], n=3, cutoff=0.6) -> list[str]:
    norm_titles = [norm_key(t) for t in titles]
    m = difflib.get_close_matches(norm_key(query), norm_titles, n=n, cutoff=cutoff)
    out = []
    for nk in m:
        for t in titles:
            if norm_key(t) == nk and t not in out:
                out.append(t)
                break
    return out

def render_book_line(b: dict) -> str:
    return (
        f"[BOOK_ID] **{b['id']}** — [TITLE] **{b['title']}** — "
        f"[AUTHOR] {b['author']} — [CATEGORY] {b['category']} — "
        f"[PRICE] {fmt_price(b['price'])} — [STOCK] {b['stock']} cuốn"
    )

# ---------------- DATABASE HELPERS ----------------
def get_all_books():
    """Trả về list[dict] (tránh DetachedInstanceError)."""
    try:
        from app.db import get_db_session
        from app.models import Book
        from sqlalchemy import select
        with get_db_session() as session:
            rows = session.execute(select(Book)).scalars().all()
            return [
                {
                    "id": b.id, "title": b.title, "author": b.author,
                    "price": float(b.price), "stock": int(b.stock),
                    "category": b.category,
                } for b in rows
            ]
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def get_book_by_id(book_id: int):
    for b in get_all_books():
        if b["id"] == book_id:
            return b
    return None

def smart_search_books_exact(query: str):
    """So khớp *chính xác* theo title/author/category (không phân biệt dấu)."""
    books = get_all_books()
    q = norm_key(query)
    return [
        b for b in books
        if q in (norm_key(b["title"]), norm_key(b["author"]), norm_key(b["category"]))
    ]

def search_by_author(author: str):
    q = norm_key(author)
    return [b for b in get_all_books() if q in norm_key(b["author"])]

def search_by_category(cat: str):
    q = norm_key(cat)
    return [b for b in get_all_books() if q in norm_key(b["category"])]

def help_titles_md():
    titles = [b["title"] for b in get_all_books()]
    return "\n".join([f"- {t}" for t in titles]) if titles else "- (Chưa có dữ liệu)"

def fetch_orders():
    """Join Orders + Book title để hiển thị admin."""
    try:
        from app.db import get_db_session
        from app.models import Order, Book
        from sqlalchemy import select, desc
        with get_db_session() as session:
            rows = session.execute(
                select(Order, Book.title).join(Book, Book.id == Order.book_id).order_by(desc(Order.created_at))
            ).all()
            out = []
            for o, title in rows:
                out.append({
                    "id": o.id, "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
                    "title": title, "qty": o.quantity, "customer": o.customer_name,
                    "phone": o.phone, "address": o.address, "status": o.status,
                })
            return out
    except Exception as e:
        st.error(f"Load orders error: {e}")
        return []

def update_order_status(order_id: int, new_status: str):
    """
    Rules về tồn kho khi đổi trạng thái:
    - prev != 'canceled'  and new == 'canceled'  -> +stock (hoàn kho)
    - prev == 'canceled'  and new in active set  -> -stock lại (nếu đủ)
    - các trường hợp khác -> không động tới stock
    """
    try:
        from app.db import get_db_session
        from app.models import Order, Book
        from sqlalchemy import select

        def canon(s: str) -> str:
            s = (s or "").strip().lower()
            return {"cancelled": "canceled"}.get(s, s)

        with get_db_session() as session:
            od = session.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
            if not od:
                return False, "Order not found"

            prev = canon(od.status)
            new  = canon(new_status)
            if prev == new:
                return True, "No change"

            bk = session.execute(select(Book).where(Book.id == od.book_id)).scalar_one_or_none()
            if not bk:
                return False, "Book not found for the order"

            if prev != "canceled" and new == "canceled":
                bk.stock += od.quantity
            elif prev == "canceled" and new in {"pending", "confirmed", "shipped"}:
                if bk.stock >= od.quantity:
                    bk.stock -= od.quantity
                else:
                    return False, f"Không đủ tồn kho để mở lại đơn (cần {od.quantity}, còn {bk.stock})."

            od.status = new
            return True, "Updated"
    except Exception as e:
        return False, str(e)

# ---------------- RULE-BASED NLU ----------------
def rule_nlu(user_text: str) -> dict:
    """
    {"intent": "order|search|unknown", "book_title": "", "quantity": None, "customer_name": ""}
    """
    text = " " + norm_key(user_text) + " "
    titles = [b["title"] for b in get_all_books()]
    authors = [b["author"] for b in get_all_books()]
    categories = [b["category"] for b in get_all_books()]

    intent = "unknown"
    book_title, qty, name = "", None, ""

    m_qty = re.search(r"(?:\b(?:mua|dat|order|lay)\b[^0-9]{0,10})?(\d+)\s*(?:cuon|quyen|x)?", text)
    if m_qty:
        try:
            qty = max(1, int(m_qty.group(1)))
        except Exception:
            qty = None

    if re.search(r"\b(dat|mua|order|lay|mua giup|muon mua)\b", text):
        intent = "order"
    elif re.search(r"\b(tim|kiem|co|con|xem|tra cuu)\b", text) or "sach cua" in text:
        intent = "search"

    m_name = re.search(r"(toi la|tên|ten|cho)\s+([a-zA-ZÀ-ỹ\s]{2,})", strip_accents(user_text), flags=re.IGNORECASE)
    if m_name:
        name = m_name.group(2).strip().title()

    for t in titles:
        if f" {norm_key(t)} " in text:
            book_title = t; break
    if not book_title:
        for a in authors:
            if f" {norm_key(a)} " in text or f" sach cua {norm_key(a)} " in text:
                found = search_by_author(a)
                if found: book_title = found[0]["title"]; break
    if not book_title:
        for c in categories:
            if f" {norm_key(c)} " in text:
                found = search_by_category(c)
                if found: book_title = found[0]["title"]; break
    if not book_title:
        sugg = fuzzy_suggest(user_text, titles, n=1, cutoff=0.65)
        if sugg: book_title = sugg[0]

    return {"intent": intent, "book_title": book_title, "quantity": qty, "customer_name": name}

# --------- PARSER MỆNH LỆNH ĐẶT HÀNG (chắc chắn vào flow đặt) ---------
ORDER_VERB_RE = re.compile(r"(?:^|\s)(dat|mua|order|lay)\b", re.IGNORECASE)
def parse_order_command(raw: str):
    """
    Trả về (book_query:str, qty_hint:Optional[int]) nếu phát hiện 'đặt/mua ...', ngược lại (None, None).
    Bắt cả mẫu: 'đặt 2 (cuốn|quyển|x) <tên sách>'
    """
    noacc = strip_accents(raw).lower().strip()
    m = ORDER_VERB_RE.search(noacc)
    if not m:
        return None, None
    tail = noacc[m.end():].strip()
    if not tail:
        return "", None
    m2 = re.match(r"(\d+)\s*(?:cuon|quyen|x)?\s*(.*)", tail)
    qty_hint, book_query = None, tail
    if m2:
        try:
            qty_hint = max(1, int(m2.group(1)))
        except Exception:
            qty_hint = None
        book_query = (m2.group(2) or "").strip()
    return book_query, qty_hint

# ===== Admin utility: delete ALL orders & reset stocks to seed =====
def admin_delete_all_orders_and_reset_to_seed():
    """
    Xoá toàn bộ đơn và đưa tồn kho về đúng số lượng gốc định nghĩa trong app.seed.SAMPLE_BOOKS.
    """
    try:
        from app.db import get_db_session
        from app.models import Order, Book
        from app.seed import SAMPLE_BOOKS
        from sqlalchemy import select, delete

        with get_db_session() as session:
            # Reset stock theo seed (match bằng title)
            for sb in SAMPLE_BOOKS:
                row = session.execute(select(Book).where(Book.title == sb["title"])).scalar_one_or_none()
                if row:
                    row.stock = int(sb["stock"])
            # Xoá tất cả orders
            session.execute(delete(Order))
            return True, "Đã xoá toàn bộ đơn và reset tồn kho về giá trị gốc (seed)."
    except Exception as e:
        return False, str(e)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.subheader("⚙️ Tips")
    st.write("- Tra cứu theo **ID**: gõ `12` hoặc `id: 12`")
    st.write("- Tra cứu theo **author**: gõ tên tác giả (VD: `Dale Carnegie`)")
    st.write("- Tra cứu theo **category**: gõ `Ky nang`, `Khoa hoc`, ...")
    st.markdown("---")
    st.caption("Quick Titles")
    st.write(help_titles_md())

# ---------------- TABS ----------------
tab_chat, tab_admin = st.tabs(["💬 Chat", "🛠️ Admin"])

# ====================== CHAT TAB ======================
with tab_chat:
    st.info("Gõ **đặt <tên sách>** (có thể kèm số lượng: *đặt 2 cuốn ...*) để mua. Nếu thiếu, hệ thống sẽ hỏi tiếp **số lượng → tên → SĐT & địa chỉ**.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"""Xin chào! Tôi là trợ lý của BookStore.

Tra cứu:
- Theo ID: gõ số hoặc `id: <số>`
- Theo tiêu đề/author/category (không phân biệt dấu)
- Ví dụ: `Dale Carnegie`, `Ky nang`, `Dac Nhan Tam`

Đặt hàng:
- Gõ **đặt <tên sách>** hoặc câu tự nhiên: "mua 2 cuốn Dac Nhan Tam"

Sách hiện có:
{help_titles_md()}
""",
        }]

    if "order_flow" not in st.session_state:
        st.session_state.order_flow = None  # {'step','book','qty','name'}

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Nhập yêu cầu…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        user_input = prompt.strip()
        response = ""
        books_now = get_all_books()
        nk = norm_key(user_input)

        # ---- ƯU TIÊN: MỆNH LỆNH ĐẶT HÀNG ----
        book_query, qty_hint = parse_order_command(user_input)
        if book_query is not None:
            found = smart_search_books_exact(book_query)
            if not found:
                titles = [x["title"] for x in books_now]
                sugg = fuzzy_suggest(book_query, titles, n=3, cutoff=0.55)
                if len(sugg) == 1:
                    found = smart_search_books_exact(sugg[0])

            if len(found) == 1:
                b = found[0]
                st.session_state.order_flow = {"step": "ask_qty", "book": b}
                preset = ""
                if isinstance(qty_hint, int) and 1 <= qty_hint <= b["stock"]:
                    st.session_state.order_flow["qty"] = qty_hint
                    st.session_state.order_flow["step"] = "ask_name"
                    preset = f"[PRESET] Số lượng: {qty_hint}\n"

                next_line = "Nhập **tên khách hàng**." if "qty" in st.session_state.order_flow else f"Nhập **số lượng** (1–{b['stock']})."
                response = f"""[ORDER] Chuẩn bị đặt hàng:

{render_book_line(b)}
{preset}[NEXT] {next_line}"""
            elif len(found) == 0:
                titles = [x["title"] for x in books_now]
                sugg = fuzzy_suggest(book_query, titles, n=3, cutoff=0.55)
                bullet = "\n".join(f"- {s}" for s in sugg) if sugg else "- (không có gợi ý gần)"
                response = f"[NOT_FOUND] Không tìm thấy sách '{book_query}'.\n\n[GỢI Ý]\n{bullet}"
            else:
                response = "[ERROR] Nhiều kết quả. Gõ tên chính xác hoặc chọn theo ID."
        else:
            # ---- ORDER FLOW ----
            flow = st.session_state.order_flow
            if flow and flow.get("step") == "ask_qty":
                if user_input.isdigit():
                    qty = int(user_input)
                    if 1 <= qty <= flow["book"]["stock"]:
                        flow["qty"] = qty
                        flow["step"] = "ask_name"
                        response = "[INPUT] Vui lòng nhập **tên khách hàng**."
                    else:
                        response = f"[WARNING] Số lượng phải từ 1 đến {flow['book']['stock']}."
                else:
                    response = "[WARNING] Vui lòng nhập **số nguyên** cho số lượng."
            elif flow and flow.get("step") == "ask_name":
                if len(user_input) >= 2:
                    flow["name"] = user_input
                    flow["step"] = "ask_contact"
                    response = "[INPUT] Nhập **SĐT và địa chỉ** (VD: `0123456789 Ha Noi`)."
                else:
                    response = "[WARNING] Tên quá ngắn. Vui lòng nhập lại."
            elif flow and flow.get("step") == "ask_contact":
                tokens = user_input.split()
                if tokens:
                    phone_raw = tokens[0]
                    phone = re.sub(r"\D", "", phone_raw)  # chỉ giữ chữ số
                    address = " ".join(tokens[1:]).strip()
                    if not (9 <= len(phone) <= 11) or len(address) < 3:
                        response = "[WARNING] Nhập **SĐT (9–11 số)** và **địa chỉ** hợp lệ. Ví dụ: `0123456789 Ha Noi`"
                    else:
                        try:
                            from app.db import get_db_session
                            from app.models import Book, Order

                            with get_db_session() as session:
                                book = session.get(Book, flow["book"]["id"])
                                if book and book.stock >= flow["qty"]:
                                    session.add(
                                        Order(
                                            customer_name=flow["name"], phone=phone, address=address,
                                            book_id=book.id, quantity=flow["qty"], status="pending",
                                        )
                                    )
                                    book.stock -= flow["qty"]
                                    response = f"""[SUCCESS] ĐẶT HÀNG THÀNH CÔNG!

{render_book_line({"id": book.id, "title": book.title, "author": book.author, "category": book.category, "price": float(book.price), "stock": book.stock})}
[QTY] {flow["qty"]}
[CUSTOMER] {flow["name"]}
[CONTACT] {phone} | {address}
"""
                                    st.session_state.order_flow = None
                                else:
                                    response = "[ERROR] Sách không đủ tồn kho."
                        except Exception as e:
                            response = f"[ERROR] Lỗi đặt hàng: {e}"
                else:
                    response = "[WARNING] Nhập SĐT và địa chỉ."
            else:
                # ---- TRA CỨU ----
                id_match = re.match(r"^(?:id:\s*)?(\d+)$", nk)
                if id_match:
                    b = get_book_by_id(int(id_match.group(1)))
                    if b:
                        response = f"[FOUND] Tìm thấy theo ID:\n\n{render_book_line(b)}\n\n[ORDER] Gõ: **đặt {b['title']}**"
                    else:
                        response = "[NOT_FOUND] Không có sách với ID đó."
                else:
                    exact = smart_search_books_exact(user_input)
                    if len(exact) == 1:
                        b = exact[0]
                        response = f"[FOUND] Tìm thấy:\n\n{render_book_line(b)}\n\n[ORDER] Gõ: **đặt {b['title']}**"
                    elif len(exact) > 1:
                        lines = "\n".join(f"- {render_book_line(b)}" for b in exact)
                        response = f"[FOUND] Có {len(exact)} sách phù hợp:\n\n{lines}\n\n[ORDER] Gõ: **đặt <tên sách>**"
                    else:
                        nlu = rule_nlu(user_input)
                        if nlu and nlu.get("book_title"):
                            found = smart_search_books_exact(nlu["book_title"])
                            if found:
                                b = found[0]
                                if nlu.get("intent") == "search":
                                    response = f"[FOUND] Tìm thấy:\n\n{render_book_line(b)}\n\n[ORDER] Gõ: **đặt {b['title']}**"
                                else:
                                    flow = {"step": "ask_qty", "book": b}
                                    if isinstance(nlu.get("quantity"), int) and 1 <= nlu["quantity"] <= b["stock"]:
                                        flow["qty"] = nlu["quantity"]; flow["step"] = "ask_name"
                                    if nlu.get("customer_name"):
                                        flow["name"] = nlu["customer_name"]
                                        if "qty" in flow: flow["step"] = "ask_contact"
                                    st.session_state.order_flow = flow
                                    preset = ""
                                    if "qty" in flow:  preset += f"[PRESET] Số lượng: {flow['qty']}\n"
                                    if "name" in flow: preset += f"[PRESET] Tên KH: {flow['name']}\n"
                                    next_line = {
                                        "ask_qty": f"Nhập **số lượng** (1–{b['stock']})",
                                        "ask_name": "Nhập **tên khách hàng**",
                                        "ask_contact": "Nhập **SĐT và địa chỉ** (VD: `0123456789 Ha Noi`)",
                                    }[flow["step"]]
                                    response = f"""[ORDER] Chuẩn bị đặt hàng:

{render_book_line(b)}
{preset}[NEXT] {next_line}"""
                            else:
                                response = "[NOT_FOUND] Không map được vào DB."
                        else:
                            titles = [x["title"] for x in books_now]
                            sugg = fuzzy_suggest(user_input, titles)
                            bullet = "\n".join(f"- {s}" for s in sugg) if sugg else "- (không có gợi ý gần)"
                            response = f"[NOT_FOUND] Không tìm thấy.\n\n[GỢI Ý]\n{bullet}"

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ====================== ADMIN TAB ======================
with tab_admin:
    st.subheader("🧾 Orders")
    orders = fetch_orders()
    if orders:
        st.dataframe(orders, use_container_width=True)
        st.markdown("### Cập nhật trạng thái")
        order_options = {f"#{o['id']} | {o['title']} | {o['status']}": o['id'] for o in orders}
        sel_label  = st.selectbox("Chọn đơn", list(order_options.keys())) if order_options else None
        new_status = st.selectbox("Trạng thái mới", ["pending", "confirmed", "canceled", "shipped"])
        if st.button("Cập nhật") and sel_label:
            ok, msg = update_order_status(order_options[sel_label], new_status)
            if ok: st.success("Đã cập nhật!"); st.rerun()
            else:  st.error(f"Cập nhật lỗi: {msg}")
    else:
        st.info("Chưa có đơn hàng.")

    st.markdown("---")
    st.subheader("📚 Books (read-only)")
    books = get_all_books()
    if books:
        st.dataframe(
            [
                {"book_id": b["id"], "title": b["title"], "author": b["author"],
                 "category": b["category"], "price": fmt_price(b["price"]), "stock": b["stock"],}
                for b in books
            ],
            use_container_width=True,
        )
    else:
        st.info("Chưa có sách.")

    st.markdown("---")
    st.subheader("🧨 Danger Zone")
    if st.button("❗ Delete ALL orders & Reset stock to SEED"):
        ok, msg = admin_delete_all_orders_and_reset_to_seed()
        if ok: st.success(msg); st.rerun()
        else:  st.error(msg)

# ---------------- Danh sách DB ở phần đầu trang ----------------
st.markdown("### [DB] Database BookStore có:")
if "show_books" not in st.session_state:
    with st.expander("Xem danh sách sách trong database", expanded=False):
        for b in get_all_books():
            st.markdown("- " + render_book_line(b))
    st.session_state.show_books = True
