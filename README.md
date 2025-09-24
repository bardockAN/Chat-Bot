## Chatbot nha sach - Huong dan cho nguoi moi

### 1) Yeu cau
- Windows 10/11, Python 3.10+ da cai san (go `python --version`).

### 2) Tao moi truong va cai thu vien
Mo PowerShell tai thu muc `D:\chatbot` va chay:

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Neu `requirements.txt` chua co, ban co the tao nhanh:

```powershell
@'
tabulate==0.9.0
regex==2024.4.16
SQLAlchemy==2.0.36
colorama==0.4.6
'@ | Set-Content requirements.txt
```

### 3) Khoi tao database va du lieu mau

```powershell
python -m app.seed
```

Lan dau se tao file `data/bookstore.db` va chen mot vai quyen sach mau.

### 4) Chay chatbot

```powershell
python -m app.chat
```

### 4b) Chay giao dien web (Flask)

```powershell
python -m app.web
```
- Mo trinh duyet: `http://localhost:8000`

### 4c) Chay giao dien Streamlit (tuy chon)

```powershell
streamlit run app/streamlit_app.py
```
- Streamlit se mo trang web o dia chi hien thi trong console (thuong la `http://localhost:8501`).

### 5) Goi y cau lenh
- Tim theo ten: `tim Dac Nhan Tam`
- Tim theo tac gia: `tac gia Paulo Coelho`
- Tim theo the loai: `the loai van hoc`
- Dat hang: `dat sach Nha Gia Kim 2 quyen`

Bot se hoi tiep cac thong tin con thieu: ho ten, so dien thoai, dia chi.

### 6) Giai thich nhanh
- Thu muc `app/` chua: `db.py` (ket noi SQLite), `models.py` (bang `books`, `orders`), `seed.py` (chen du lieu mau), `nlu.py` (nhan dien y dinh bang quy tac), `chat.py` (vong lap hoi-dap console), `web.py` + `templates/index.html` (giao dien web).

### 7) Deploy nhanh (tuy chon)
- Render/Railway: tao service Python, set start command: `python -m app.web`.
- Luu y: SQLite la file cuc bo; de dung tren cloud nhe nhe co the van OK cho demo, hoac chuyen sang PostgreSQL neu can.


