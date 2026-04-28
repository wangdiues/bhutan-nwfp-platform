"""
Gunicorn configuration for Bhutan NWFP Digital Marketplace & Management Platform.

Worker model: gthread (thread-based) — suits a Django app that mixes I/O
(database queries, file uploads) with CPU-light request handling.

Tune via environment variables or by editing this file before deployment.

Reference: https://docs.gunicorn.org/en/stable/settings.html
"""

import multiprocessing

# ---------------------------------------------------------------------------
# Server socket
# ---------------------------------------------------------------------------
# Bind to all interfaces on port 8000; Nginx handles external exposure.
bind = "0.0.0.0:8000"

# ---------------------------------------------------------------------------
# Worker processes
# ---------------------------------------------------------------------------
# Recommended formula: (2 × CPU cores) + 1
# This is a safe default; reduce if the host has limited RAM.
workers = multiprocessing.cpu_count() * 2 + 1

# Use gthread workers for better handling of concurrent slow requests
worker_class = "gthread"

# Threads per worker — each handles one request concurrently
threads = 2

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
# Workers silent for more than this many seconds are killed and restarted
timeout = 60

# After this many seconds waiting for a response from the server, the
# keepalive connection is closed (must be less than Nginx keepalive_timeout)
keepalive = 2

# ---------------------------------------------------------------------------
# Worker lifecycle — prevents memory leaks
# ---------------------------------------------------------------------------
# Restart each worker after handling this many requests
max_requests = 1000

# Jitter prevents all workers from restarting simultaneously
max_requests_jitter = 50

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# '-' means log to stdout/stderr (captured by Docker / systemd)
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Include worker process IDs in access log for debugging multi-worker issues
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# ---------------------------------------------------------------------------
# Process naming
# ---------------------------------------------------------------------------
proc_name = "nwfp_platform"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# Limit the number of headers to prevent header-based DoS
limit_request_fields = 100
limit_request_field_size = 8190
limit_request_line = 4094
