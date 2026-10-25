import os

bind = "0.0.0.0:8080"
# One process keeps the in-process cache coherent; the thread pool provides
# concurrency for DB waits without multiplying cache copies.
workers = int(os.getenv("GUNICORN_WORKERS", "1"))
threads = int(os.getenv("GUNICORN_THREADS", "8"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "25"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "10"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
