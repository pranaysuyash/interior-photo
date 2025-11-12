"""
Gunicorn production configuration for Interior AI API

This configuration is optimized for production deployment with:
- Multiple worker processes for handling concurrent requests
- Proper logging configuration
- Worker lifecycle management
- Health checks and graceful restarts
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'uvicorn.workers.UvicornWorker'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Worker lifecycle
graceful_timeout = 30
preload_app = True

# Logging
accesslog = '/app/logs/gunicorn_access.log' if os.path.exists('/app/logs') else '-'
errorlog = '/app/logs/gunicorn_error.log' if os.path.exists('/app/logs') else '-'
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'interior-ai-api'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = os.getenv('SSL_KEYFILE')
certfile = os.getenv('SSL_CERTFILE')
ca_certs = os.getenv('SSL_CA_CERTS')

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Interior AI API server")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Interior AI API server")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Interior AI API server is ready. Spawning workers")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")


def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")


def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass


def child_exit(server, worker):
    """Called just after a worker has been exited, in the master process."""
    server.log.info(f"Worker exited (pid: {worker.pid})")


def worker_exit(server, worker):
    """Called just after a worker has been exited, in the worker process."""
    pass


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Number of workers changed from {old_value} to {new_value}")


def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Interior AI API server")
