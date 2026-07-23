"""Gunicorn configuration.

Removes the ``Server: gunicorn`` response header so the stack is not advertised.
"""
import gunicorn

# Blanking this removes the Server header gunicorn would otherwise send.
gunicorn.SERVER_SOFTWARE = ''
gunicorn.SERVER = ''
