"""
    @about: File that centralizes the wsgi application for gunicorn launch
"""
import os

from callbacks import application
from server_config import server

if __name__ == "__main__":
    application
    server
    if os.getenv("state") == "dev":
        application.run_server(debug=True, port=8000)


#    gunicorn wsgi:server -b 0.0.0.0:8050 --workers 4
