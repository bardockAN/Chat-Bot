# BookStore Chatbot (Streamlit)

Chatbot for the BookStore with a Streamlit interface and SQLite database (ORM: SQLAlchemy).  
Supports book lookup, order placement using natural language, and an admin panel for viewing/updating orders.  
LLM is optional – the application runs fully without an API key.

## Features

### Lookup & Conversation
- Search by ID (e.g., `id: <number>`).
- Exact search by title/author/genre (case-insensitive).
- Fuzzy suggestions for misspelled queries.
- Rule-based NLU: understands phrases like "buy 2 copies of Dac Nhan Tam," "books by Dale Carnegie," "genre Science," etc.

### Order Placement (Order Flow)
- Type `order <book name>` (optionally include quantity: `order 2 Dac Nhan Tam`).
- The bot will sequentially ask for quantity → customer name → phone number & address.  
  Example: `0123456789 Ha Noi`
- Creates an order (default status: pending) and updates stock.

### Admin Panel
- **Orders Table**: View orders and update statuses.
- Valid statuses: `pending`, `confirmed`, `canceled`, `shipped`.
- **Stock Rules**:
  - `prev != canceled ➜ new == canceled` → Restock.
  - `prev == canceled ➜ new in {pending, confirmed, shipped}` → Deduct stock (if sufficient).
- **Danger Zone**: Delete ALL orders & Reset stock to SEED.  
  Resets all orders and stock to initial values in `SAMPLE_BOOKS`.

### Sample Data (Seed)
- Stored in SQLite: `data/bookstore.db`.
- Initial stock:  
  `Dac Nhan Tam (15)` • `Nha Gia Kim (10)` • `Tu duy nhanh va cham (8)` • `Sach Mat Biec (20)` • `Python Co Ban (25)`.
- The app safely copies the sample DB to a writable directory if needed (safe for multi-environment runs).

## Installation & Running

### Requirements
- Python 3.10+

### Install Dependencies
```bash
pip install -r requirements.txt
```

### (Optional) Environment Variables
Create a `.env` file if needed:
```env
# Enable demo data seeding on first run (default: "1")
DEMO_MODE=1

# Only required if using the LLM module (console test or custom integration)
OPENAI_API_KEY=your_openai_api_key_here
```

### Run the Application
```bash
streamlit run streamlit_app.py
```
Open your browser at: [http://localhost:8501](http://localhost:8501)

## Quick Guide

### Lookup
- By ID: `5` or `id: 5`
- By title/author/genre: `Dac Nhan Tam`, `Dale Carnegie`, `Ky nang`, etc.

### Place Orders
- `order Python Co Ban`
- `order 2 Dac Nhan Tam`
- When prompted for phone & address, enter: `0123456789 Ha Noi`.

### Admin
- Go to the **Admin** tab → select an order → update its status (stock rules apply).
- Use **Danger Zone** → Delete ALL orders & Reset stock to SEED to reset stock to `15/10/8/20/25`.

## Project Structure
```plaintext
chatbot/
├── streamlit_app.py        # Main app (UI + chat + admin)
├── app/
│   ├── __init__.py
│   ├── db.py               # DB connection, session helper, init_db()
│   ├── models.py           # SQLAlchemy models: Book, Order
│   ├── seed.py             # SAMPLE_BOOKS + seed()
│   └── llm_chatbot.py      # (Optional) LLM engine for console/demo
├── data/
│   └── bookstore.db        # SQLite database (sample)
├── .streamlit/
│   └── secrets.toml        # (optional for Streamlit Cloud deployment)
├── .env.template           # Environment variable template
├── requirements.txt
└── README.md
```

`llm_chatbot.py` uses OpenAI GPT-3.5-turbo for console demos; not required for the Streamlit app.

### (Optional) Try LLM Console
```bash
python -m app.llm_chatbot
```
Requires `OPENAI_API_KEY` in `.env`.

## Troubleshooting

- **ImportError: circular import app.seed**  
  Resolved in the source code (no self-imports). Use the latest file.

- **No Data Visible**  
  Ensure `DEMO_MODE=1` on the first run, or use the Danger Zone to reset to seed.

- **Invalid Phone Number**  
  Must be 9–11 digits. Correct format: `0123456789 Ha Noi`.