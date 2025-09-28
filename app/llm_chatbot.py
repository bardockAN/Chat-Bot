"""
🤖 LLM-Powered BookStore Chatbot + NLU
- Bổ sung extract_intent() để trả về JSON {intent, book_title, quantity, customer_name}
"""
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import select

# Import database components
from app.db import SessionLocal, init_db
from app.models import Book, Order
from app.seed import seed

load_dotenv()


@dataclass
class BookInfo:
    title: str
    author: str
    price: float
    stock: int
    category: str
    id: Optional[int] = None


@dataclass
class OrderRequest:
    book_title: str
    quantity: int
    customer_name: str
    phone: str
    address: str


class LLMChatbot:
    """LLM-powered chatbot cho BookStore với database integration + NLU"""

    def __init__(self, api_key: Optional[str] = None, demo_seed: bool = False):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required to use LLM features.")

        self.client = OpenAI(api_key=self.api_key)
        self.conversation_history = []

        # DB init (không seed mặc định để dùng chung với app)
        init_db()
        if demo_seed:
            try:
                seed()
            except Exception:
                pass

        self.store_info = {
            "name": "BookStore",
            "description": "Nhà sách trực tuyến chuyên bán sách hay",
            "features": ["Tìm kiếm sách", "Đặt hàng", "Tư vấn sách hay", "Thông tin tác giả"],
        }

    # -------------------- DB helpers --------------------
    def get_books_from_database(self) -> List[BookInfo]:
        with SessionLocal() as session:
            books = session.execute(select(Book)).scalars().all()
            return [
                BookInfo(
                    id=b.id,
                    title=b.title,
                    author=b.author,
                    price=float(b.price),
                    stock=b.stock,
                    category=b.category,
                )
                for b in books
            ]

    # -------------------- NLU: extract_intent --------------------
    def extract_intent(self, user_text: str) -> Optional[Dict]:
        """
        Trả về dict JSON:
        {
          "intent": "search" | "order" | "unknown",
          "book_title": "<exact title or ''>",
          "quantity": <int or null>,
          "customer_name": "<string or ''>"
        }
        """
        books = self.get_books_from_database()
        titles = [b.title for b in books]
        titles_txt = "\n".join(f"- {t}" for t in titles)

        system = (
            "Bạn là NLU cho BookStore. "
            "Nhiệm vụ: trích xuất ý định (intent) và các slot từ câu người dùng. "
            "Chỉ được chọn book_title từ danh sách TITLES bên dưới; nếu không khớp, để rỗng. "
            "Trả về JSON **duy nhất**, không thêm chữ nào khác.\n\n"
            "Các intent:\n"
            "- 'order': người dùng muốn đặt mua một cuốn trong TITLES. Có thể chứa quantity và customer_name.\n"
            "- 'search': người dùng muốn tra cứu / hỏi về sách nào đó trong TITLES.\n"
            "- 'unknown': không thuộc 2 loại trên.\n\n"
            "JSON schema:\n"
            '{"intent":"...", "book_title":"...", "quantity":null, "customer_name":""}\n\n'
            "TITLES:\n"
            f"{titles_txt}\n"
        )

        try:
            resp = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
                max_tokens=200,
            )
            raw = resp.choices[0].message.content.strip()
            # Cố gắng bóc JSON
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                raw = raw[start : end + 1]
            data = json.loads(raw)
            # Sanitize keys
            for k in ["intent", "book_title", "customer_name"]:
                data[k] = data.get(k) or ""
            if "quantity" not in data:
                data["quantity"] = None
            return data
        except Exception:
            return None

    # -------------------- (demo) Chat text --------------------
    def _create_system_prompt(self) -> str:
        available_books = self.get_books_from_database()
        books_info = "\n".join(
            f"- {b.title} ({b.author}) - {b.price:,.0f}đ - Còn: {b.stock} - Thể loại: {b.category}"
            for b in available_books
        )
        return f"""
🤖 Bạn là AI assistant của BookStore.

SÁCH CÓ SẴN:
{books_info}

NHIỆM VỤ:
1. Tìm kiếm/giới thiệu sách
2. Hỗ trợ đặt hàng (hỏi thêm thông tin nếu thiếu)

Luôn trả lời thân thiện, hữu ích.
"""

    def chat(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": self._create_system_prompt()}] + self.conversation_history[-10:]
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", messages=messages, max_tokens=500, temperature=0.7
            )
            ai_response = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        except Exception as e:
            return f"Xin lỗi, tôi gặp lỗi kỹ thuật: {e}"
