"""
Web App service
----------------
This is a small Flask website. Its only special job, for this lab, is to
call the REST API service (the other container) over the network and show
the result. This is the core idea of distributed systems: two independent
programs, running in two independent containers, talking to each other
over a network instead of calling each other's functions directly.
"""

import os
import socket

import requests
from flask import Flask, render_template

app = Flask(__name__)

# The API_URL is read from an environment variable so that the SAME code
# can talk to the API differently depending on how it's run:
#   - when run with docker compose, this will be "http://api:5001"
#     ("api" is the service name defined in docker-compose.yml)
#   - if not set, it falls back to localhost (useful for local testing)
API_URL = os.environ.get("API_URL", "http://localhost:5001")


@app.route("/")
def home():
    # socket.gethostname() returns the container's hostname.
    # In Docker, a container's hostname is its container ID by default.
    # This is useful later when we scale to multiple web containers,
    # you'll SEE a different hostname per container/tab refresh.
    hostname = socket.gethostname()

    try:
        response = requests.get(f"{API_URL}/api/students", timeout=3)
        response.raise_for_status()
        students = response.json()
        api_status = "connected"
    except Exception as exc:  # noqa: BLE001 - fine for a teaching example
        students = []
        api_status = f"could not reach API ({exc})"

    return render_template(
        "index.html",
        hostname=hostname,
        students=students,
        api_status=api_status,
        api_url=API_URL,
    )


if __name__ == "__main__":
    # host="0.0.0.0" is REQUIRED inside Docker containers.
    # "0.0.0.0" means "listen on every network interface", so the
    # request can reach the app from outside the container.
    # If you use "127.0.0.1" here, the app will refuse outside connections
    # and your browser will show "connection reset" / "can't be reached".
    app.run(host="0.0.0.0", port=5000, debug=True)
