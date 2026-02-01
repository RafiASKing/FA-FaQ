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

# --- PORTS ---
# 8501 = App User (Streamlit)
# 8502 = App Admin (Streamlit)
# 8000 = Bot WA (FastAPI)
# 8080 = Web V2 (FastAPI)
EXPOSE 8501 8502 8000 8080

# Command default (akan ditimpa oleh docker-compose)
CMD ["streamlit", "run", "streamlit_apps/user_app.py", "--server.port=8501", "--server.address=0.0.0.0"]