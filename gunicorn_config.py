# gunicorn_config.py - Configuración robusta para evitar errores 502
import os
import multiprocessing

# Configuración del servidor
bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
workers = min(2, multiprocessing.cpu_count())
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 60

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Preload
preload_app = True

# Restart workers
max_worker_memory = 1024 * 1024 * 1024  # 1GB

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

def post_fork(server, worker):
    """Configuración después de fork del worker"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Configuración antes de fork del worker"""
    server.log.info("Worker about to be forked (pid: %s)", worker.pid)

def when_ready(server):
    """Callback cuando el servidor está listo"""
    server.log.info("MERLIN server is ready. Listening on: %s", server.address)

def worker_int(worker):
    """Callback cuando worker recibe SIGINT"""
    worker.log.info("worker received INT or QUIT signal")

def pre_exec(server):
    """Callback antes de exec"""
    server.log.info("Forked child, re-executing.")

def on_exit(server):
    """Callback al salir"""
    server.log.info("MERLIN server is shutting down.") 