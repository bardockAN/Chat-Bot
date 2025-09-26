# 📚 Chatbot Nhà Sách BookStore

Hệ thống chatbot thông minh hỗ trợ tìm kiếm và đặt mua sách bằng tiếng Việt tự nhiên.

🌟 **[Trải nghiệm ngay tại đây](https://9qzwnzxnujruw4nv9m5izj.streamlit.app/)** - Không cần cài đặt!

## ✨ Tính Năng

- 🔍 **Tìm kiếm sách**: Theo tên sách, tác giả, thể loại
- 🛒 **Đặt hàng thông minh**: Ghi nhận thông tin đơn hàng đầy đủ
- 💬 **Giao tiếp tự nhiên**: Nhận diện ngôn ngữ Việt với dấu
- 🖥️ **Đa giao diện**: Console, Web (Flask), Streamlit
- 💾 **Cơ sở dữ liệu**: SQLite với auto-seed dữ liệu mẫu

## 🚀 Cài Đặt Nhanh

### Yêu Cầu Hệ Thống
- Windows 10/11 hoặc macOS/Linux
- Python 3.10+ (kiểm tra: `python --version`)

### 1. Thiết Lập Môi Trường

```powershell
# Clone repository (nếu chưa có)
git clone https://github.com/bardockAN/Chat-Bot.git
cd Chat-Bot

# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows)
.\.venv\Scripts\Activate.ps1

# Hoặc trên macOS/Linux
# source .venv/bin/activate

# Cài đặt thư viện
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Khởi Tạo Dữ Liệu

```powershell
# Tạo database và thêm sách mẫu
python -m app.seed
```

## 🎮 Cách Sử Dụng

### 🖥️ Console (Giao diện dòng lệnh)
```powershell
python -m app.chat
```

### 🌐 Web App (Flask)
```powershell
python -m app.web
```
Mở trình duyệt: http://localhost:8000

### ⚡ Streamlit (Giao diện hiện đại)
```powershell
streamlit run app/streamlit_app.py
```
- **Local**: http://localhost:8501
- **Live Demo**: https://9qzwnzxnujruw4nv9m5izj.streamlit.app/

## 💬 Ví Dụ Câu Lệnh

| Mục đích | Ví dụ |
|----------|-------|
| **Tìm theo tên** | `tìm Đắc Nhân Tâm` |
| **Tìm theo tác giả** | `tác giả Paulo Coelho` |
| **Tìm theo thể loại** | `thể loại văn học` |
| **Đặt hàng** | `đặt sách Nhà Giả Kim 2 quyển` |

Bot sẽ hỏi thêm: họ tên, số điện thoại, địa chỉ để hoàn tất đơn hàng.

## 🏗️ Cấu Trúc Dự Án

```
📦 Chat-Bot/
├── 📁 app/
│   ├── 🗃️ db.py              # Kết nối SQLite
│   ├── 📋 models.py          # Models: Book, Order
│   ├── 🌱 seed.py            # Dữ liệu mẫu
│   ├── 🧠 nlu.py             # Xử lý ngôn ngữ tự nhiên
│   ├── 💬 chat.py            # Console interface
│   ├── 🌐 web.py             # Flask web app
│   ├── ⚡ streamlit_app.py   # Streamlit interface
│   └── 📁 templates/         # HTML templates
├── 📁 data/                  # SQLite database
├── 📋 requirements.txt       # Python dependencies
└── 📖 README.md             # Tài liệu này
```

## 🚀 Deploy Production

### Streamlit Cloud ⭐ (Recommended)
1. Push code lên GitHub
2. Kết nối repo với [Streamlit Cloud](https://streamlit.io/cloud)
3. Main file: `app/streamlit_app.py`
4. Deploy tự động!

**Demo đang chạy**: https://9qzwnzxnujruw4nv9m5izj.streamlit.app/

### Render/Railway
```bash
# Build command
pip install -r requirements.txt

# Start command (Flask)
python -m app.web

# Hoặc (Streamlit)
streamlit run app/streamlit_app.py --server.port=$PORT
```

## 🛠️ Kỹ Thuật

- **Backend**: SQLAlchemy ORM, SQLite
- **NLU**: Rule-based với regex patterns
- **Web**: Flask + Bootstrap 5
- **Modern UI**: Streamlit
- **Vietnamese**: Unicode normalization

## 📝 Cơ Sở Dữ Liệu

### Books
```sql
book_id, title, author, price, stock, category
```

### Orders  
```sql
order_id, customer_name, phone, address, book_id, quantity, status, created_at
```

## 🤝 Đóng Góp

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/ten-tinh-nang`
3. Commit: `git commit -m "Thêm tính năng mới"`
4. Push: `git push origin feature/ten-tinh-nang`
5. Tạo Pull Request

## 📄 License

MIT License - Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

💡 **Mẹo**: Thử hỏi bot bằng nhiều cách khác nhau - nó hiểu khá thông minh!


