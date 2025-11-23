# Gunakan Python versi ringan
FROM python:3.10-slim

# Set folder kerja
WORKDIR /app

# Install build tools (PENTING untuk ChromaDB & pysqlite3)
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

# Beritahu Docker bahwa kita akan pakai port ini
EXPOSE 8501 8502

# Command default (akan ditimpa oleh docker-compose)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]