# Gunakan Python 3.10 slim
FROM python:3.10-slim

# Set folder kerja
WORKDIR /app

# Set PYTHONPATH so imports work from any subdirectory
ENV PYTHONPATH=/app

# Install build tools for compiling Python packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN groupadd -r fafaq && useradd -r -g fafaq -d /app -s /sbin/nologin fafaq

# Copy seluruh kode proyek
COPY . .

# Ensure data and images dirs exist and are writable
RUN mkdir -p /app/data/logs /app/images && \
    chown -R fafaq:fafaq /app/data /app/images

# Switch to non-root user
USER fafaq

# --- PORTS ---
# 8501 = App User (Streamlit)
# 8502 = App Admin (Streamlit)
# 8000 = Bot WA (FastAPI)
# 8080 = Web V2 (FastAPI)
EXPOSE 8501 8502 8000 8080

# Health check (default FastAPI health endpoint)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command default (akan ditimpa oleh docker-compose)
CMD ["streamlit", "run", "streamlit_apps/user_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
