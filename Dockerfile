FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 wespa && chown -R wespa:wespa /app
USER wespa

# Expose port
EXPOSE 8080

# Run with gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
