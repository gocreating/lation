bind = "0.0.0.0:8000"
workers = 1
# worker_class = "gevent"
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = "warning"
keyfile = "./deploy/certificates/privkey1.pem"
certfile = "./deploy/certificates/fullchain1.pem"