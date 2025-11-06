# =========================
# Stage 1: Builder
# =========================
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# =========================
# Stage 2: Runtime
# =========================
FROM python:3.11-slim

WORKDIR /app

# Install LibreOffice for DOCX→PDF conversion
RUN apt-get update && apt-get install -y libreoffice && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy project files
COPY . .

# Fix line endings and permissions
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix /app/gunicorn_start.sh && \
    chmod +x /app/gunicorn_start.sh && \
    apt-get purge -y dos2unix && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

VOLUME ["/tmp"]

CMD ["/app/gunicorn_start.sh"]
