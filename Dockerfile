# Gunakan Python 3.10 slim
FROM python:3.10-slim

# Set folder kerja
WORKDIR /app

# Install build tools (PENTING untuk ChromaDB & pysqlite3)
# Kita pertahankan python3-dev dan gcc supaya aman saat compile library AI
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode proyek
COPY . .

# --- UPDATE PENTING DI SINI ---
# Buka 3 Port sekaligus:
# 8501 = App User
# 8502 = App Admin
# 8000 = Bot WA (FastAPI)
EXPOSE 8501 8502 8000

# Command default (akan ditimpa oleh docker-compose)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]