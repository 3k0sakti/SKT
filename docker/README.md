# Docker Hands-On Lab: A Playground for Distributed Systems

**Audience:** Beginners, no prior Docker experience required.
**Works on:** Windows 10/11 and macOS.
**You will build:** a Web App container and a REST API container that talk
to each other over a network, orchestrated with Docker Compose - a small,
hands-on model of a distributed system.

---

## Table of Contents

1. [Learning Objectives](#1-learning-objectives)
2. [Key Concepts (read this first)](#2-key-concepts-read-this-first)
3. [Part 0: Install Docker Desktop](#3-part-0-install-docker-desktop)
4. [Part 1: Project Structure](#4-part-1-project-structure)
5. [Part 2: Build the Web App Container](#5-part-2-build-the-web-app-container)
6. [Part 3: Build the REST API Container](#6-part-3-build-the-rest-api-container)
7. [Part 4: Orchestrate Both with Docker Compose](#7-part-4-orchestrate-both-with-docker-compose)
8. [Part 5: Testing the REST API Directly](#8-part-5-testing-the-rest-api-directly)
9. [Part 6: Distributed Systems Exercises](#9-part-6-distributed-systems-exercises)
10. [Part 7: Troubleshooting](#10-part-7-troubleshooting)
11. [Part 8: Cleaning Up](#11-part-8-cleaning-up)
12. [Part 9: What to Explore Next](#12-part-9-what-to-explore-next)

---

## 1. Learning Objectives

By the end of this lab, you will be able to:

- Explain the difference between an **image** and a **container**.
- Write a `Dockerfile` that packages an application and its dependencies.
- Run, stop, inspect, and remove containers from the command line.
- Use `docker compose` to run **multiple containers together** as one system.
- Explain how containers find and talk to each other over a Docker network
  (this is the core idea behind microservices and distributed systems).
- Scale a service to multiple container instances and observe load
  distribution - a first taste of horizontal scaling.

---

## 2. Key Concepts (read this first)

| Term | Plain-English meaning |
|---|---|
| **Image** | A read-only template/snapshot of an application plus everything it needs to run (code, runtime, libraries). Like a "recipe" or a class in OOP. |
| **Container** | A running instance of an image. Like an "object" created from a class. You can run many containers from the same image. |
| **Dockerfile** | A text file with step-by-step instructions for building an image. |
| **Docker Compose** | A tool (and a YAML file, `docker-compose.yml`) for defining and running **multiple containers together**, including how they connect to each other. |
| **Service** | In Compose terms, one entry in `docker-compose.yml` (e.g. `web`, `api`). Compose can run one or many container instances per service. |
| **Network** | A private virtual network that Docker creates so containers can find each other by name instead of by IP address. |
| **Volume** | A way to persist data outside of a container's lifecycle, so data survives even if the container is deleted. |
| **Port mapping** | Connects a port on YOUR computer (the "host") to a port INSIDE a container, so your browser can reach it. |

**Why this matters for a Distributed Systems course:** a real distributed
system is made of several independent processes that communicate over a
network, each possibly failing or restarting independently, each possibly
running as multiple replicas. Two containers talking to each other over a
Docker network - one being a web frontend, one being a backend API - is
a small, safe, local model of exactly that. Everything you practice here
(service discovery by name, ports, scaling, restart behavior, inspecting
network traffic) maps directly to real multi-node distributed systems.

---

## 3. Part 0: Install Docker Desktop

### On Windows 10/11

1. **Check your Windows edition.** Docker Desktop on Windows works best
   with **WSL2** (Windows Subsystem for Linux 2). Windows 10 (version 2004+)
   and Windows 11 both support it.
2. Download Docker Desktop from: `https://www.docker.com/products/docker-desktop/`
3. Run the installer. When prompted, make sure **"Use WSL 2 instead of
   Hyper-V"** is checked (this is the default on modern Windows and is
   recommended).
4. Restart your computer if the installer asks you to.
5. If this is your first time using WSL2, Docker Desktop may prompt you to
   install the **WSL2 Linux kernel update package**. Follow the on-screen
   link, install it, then relaunch Docker Desktop.
6. Launch **Docker Desktop** from the Start menu. Wait until the whale icon
   in the system tray stops animating and shows "Docker Desktop is running".
7. Open **PowerShell** (search "PowerShell" in the Start menu; you do NOT
   need to run it as administrator for this lab) and verify:
   ```powershell
   docker --version
   docker compose version
   ```
   Both commands should print a version number.

### On macOS

1. Check your chip: click the Apple menu > **About This Mac**. Note
   whether it says **Apple Silicon (M1/M2/M3/M4)** or **Intel**.
2. Download the matching Docker Desktop installer from:
   `https://www.docker.com/products/docker-desktop/`
   (There are separate download links for Apple Silicon and Intel - pick
   the right one.)
3. Open the downloaded `.dmg` file and drag **Docker.app** into the
   **Applications** folder.
4. Launch **Docker** from Applications (or Spotlight, `Cmd + Space` then
   type "Docker"). Grant any permission prompts (Docker needs system
   privileges to manage networking and file sharing).
5. Wait for the whale icon in the menu bar to stop animating.
6. Open **Terminal** (Spotlight > "Terminal") and verify:
   ```bash
   docker --version
   docker compose version
   ```

> **Note:** on both platforms, Docker Desktop must be **running** (the
> whale icon visible and idle) every time you use `docker` commands.
> If a command fails with something like "Cannot connect to the Docker
> daemon", it almost always means Docker Desktop is not running yet.

---

## 4. Part 1: Project Structure

Create a folder on your computer for this lab, for example
`docker-distsys-lab` on your Desktop. Inside it, we will build this exact
structure (you will create these files yourself, step by step, in Parts
2-4 below):

```
docker-distsys-lab/
├── docker-compose.yml         <- orchestrates both services
├── 01-web-app/
│   ├── Dockerfile             <- build instructions for the web app image
│   ├── requirements.txt       <- Python dependencies
│   ├── app.py                 <- the web app's source code
│   └── templates/
│       └── index.html         <- the web page shown in the browser
└── 02-rest-api/
    ├── Dockerfile             <- build instructions for the API image
    ├── requirements.txt       <- Python dependencies
    └── app.py                 <- the REST API's source code
```

**Note the key idea:** the `Dockerfile` (build instructions) is always
kept **separate** from the application code (`app.py`, `index.html`). The
Dockerfile just describes *how to package* whatever code sits next to it.
This separation is standard practice: it keeps "infrastructure" and
"application" concerns clean and easy to reason about independently.

Open your project folder in any text editor (VS Code is recommended and
free: `https://code.visualstudio.com/`) and create the folders and files
below exactly as shown.

---

## 5. Part 2: Build the Web App Container

### 5.1 Create `01-web-app/requirements.txt`

```
flask==3.0.3
requests==2.32.3
```

This lists the two Python libraries the web app needs: **Flask** (a
lightweight web framework) and **requests** (for making HTTP calls to the
API service).

### 5.2 Create `01-web-app/app.py`

```python
import os
import socket

import requests
from flask import Flask, render_template

app = Flask(__name__)

API_URL = os.environ.get("API_URL", "http://localhost:5001")


@app.route("/")
def home():
    hostname = socket.gethostname()

    try:
        response = requests.get(f"{API_URL}/api/students", timeout=3)
        response.raise_for_status()
        students = response.json()
        api_status = "connected"
    except Exception as exc:
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
    app.run(host="0.0.0.0", port=5000, debug=True)
```

**Read this carefully - two details matter a lot in Docker:**

- `host="0.0.0.0"`: this makes the app listen on every network interface
  inside the container. If you write `127.0.0.1` instead, the app will
  only accept connections *from inside the same container*, and your
  browser on the host machine will not be able to reach it at all.
- `API_URL = os.environ.get("API_URL", ...)`: the app reads the API's
  address from an **environment variable**, rather than hard-coding it.
  This is how Docker Compose will tell the web app where to find the API
  container, without changing any code.

### 5.3 Create `01-web-app/templates/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Distributed Systems Docker Lab</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; background: #0f172a; color: #e2e8f0; }
    h1 { color: #38bdf8; }
    .card { background: #1e293b; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px; }
    .ok { color: #4ade80; }
    .err { color: #f87171; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { text-align: left; padding: 8px; border-bottom: 1px solid #334155; }
    code { background: #334155; padding: 2px 6px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>🐳 Web App container</h1>

  <div class="card">
    <p><strong>This container's hostname:</strong> <code>{{ hostname }}</code></p>
    <p><strong>Talking to API at:</strong> <code>{{ api_url }}</code></p>
    <p><strong>API status:</strong>
      {% if api_status == "connected" %}
        <span class="ok">{{ api_status }}</span>
      {% else %}
        <span class="err">{{ api_status }}</span>
      {% endif %}
    </p>
  </div>

  <div class="card">
    <h2>Students (fetched live from the REST API service)</h2>
    {% if students %}
    <table>
      <tr><th>ID</th><th>Name</th><th>Course</th></tr>
      {% for s in students %}
      <tr><td>{{ s.id }}</td><td>{{ s.name }}</td><td>{{ s.course }}</td></tr>
      {% endfor %}
    </table>
    {% else %}
      <p>No data (is the <code>api</code> container running?)</p>
    {% endif %}
  </div>
</body>
</html>
```

### 5.4 Create `01-web-app/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

**Line-by-line:**

- `FROM python:3.11-slim` - start from an official, minimal Python image.
  Everything else is layered on top of this.
- `WORKDIR /app` - creates `/app` inside the container and makes it the
  "current directory" for all following instructions.
- `COPY requirements.txt .` - copies just the dependency file first
  (a deliberate ordering trick: Docker caches this layer, so if you only
  change `app.py` later, Docker won't need to reinstall dependencies).
- `RUN pip install ...` - installs the dependencies **inside the image**.
- `COPY . .` - now copies the rest of the folder's contents (app.py,
  templates/) into `/app` inside the container.
- `EXPOSE 5000` - documentation only; it does not actually publish the
  port (that happens in `docker-compose.yml` or with `docker run -p`).
- `CMD [...]` - the command that runs automatically when a container
  starts from this image.

### 5.5 Build and run the web app on its own (to test it in isolation)

Open your terminal (PowerShell on Windows, Terminal on Mac), navigate into
the `01-web-app` folder, and run:

```bash
cd docker-distsys-lab/01-web-app
docker build -t web-app-image .
```

- `docker build` reads the `Dockerfile` in the current folder (`.`) and
  builds an image.
- `-t web-app-image` tags (names) the resulting image so you can refer to
  it later.

You should see several "steps" print out, ending in something like
`Successfully tagged web-app-image:latest`.

Now run a container from that image:

```bash
docker run -p 5000:5000 --name web-app-test web-app-image
```

- `-p 5000:5000` maps port 5000 on your computer to port 5000 inside the
  container.
- `--name web-app-test` gives the container a friendly name.

Open your browser to **http://localhost:5000**. You should see the page,
but the API status will show an error - that's expected, because the API
container doesn't exist yet. Stop the container with `Ctrl + C` in the
terminal, then remove it before moving on:

```bash
docker rm web-app-test
```

---

## 6. Part 3: Build the REST API Container

### 6.1 Create `02-rest-api/requirements.txt`

```
flask==3.0.3
```

### 6.2 Create `02-rest-api/app.py`

```python
import socket

from flask import Flask, jsonify, request

app = Flask(__name__)

students = [
    {"id": 1, "name": "Ayu Lestari", "course": "Distributed Systems"},
    {"id": 2, "name": "Budi Santoso", "course": "Distributed Systems"},
    {"id": 3, "name": "Citra Dewi", "course": "Distributed Systems"},
]
next_id = 4


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "hostname": socket.gethostname()})


@app.route("/api/students", methods=["GET"])
def get_students():
    return jsonify(students)


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student)


@app.route("/api/students", methods=["POST"])
def add_student():
    global next_id
    data = request.get_json(silent=True) or {}
    if "name" not in data:
        return jsonify({"error": "field 'name' is required"}), 400

    new_student = {
        "id": next_id,
        "name": data["name"],
        "course": data.get("course", "Distributed Systems"),
    }
    students.append(new_student)
    next_id += 1
    return jsonify(new_student), 201


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json(silent=True) or {}
    student["name"] = data.get("name", student["name"])
    student["course"] = data.get("course", student["course"])
    return jsonify(student)


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    global students
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        return jsonify({"error": "Student not found"}), 404

    students = [s for s in students if s["id"] != student_id]
    return jsonify({"message": "deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
```

This is a plain REST API: `GET` to read, `POST` to create, `PUT` to
update, `DELETE` to remove - the same pattern used by real-world backend
services. Data is stored **in memory** (a Python list), so it resets every
time the container restarts. This is intentional; see the discussion
question in Part 6.

### 6.3 Create `02-rest-api/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
```

Same pattern as the web app, just a different port (5001) and no
`templates/` folder, since this service returns JSON, not HTML.

### 6.4 Build and test the API on its own

```bash
cd ../02-rest-api
docker build -t rest-api-image .
docker run -p 5001:5001 --name api-test rest-api-image
```

In a **second** terminal window/tab, test it:

```bash
curl http://localhost:5001/api/students
```

(No `curl`? You can also just open `http://localhost:5001/api/students`
directly in your browser - it will show the raw JSON.)

Stop the container (`Ctrl + C` in its terminal) and remove it:

```bash
docker rm api-test
```

---

## 7. Part 4: Orchestrate Both with Docker Compose

Testing containers one at a time with `docker run` gets tedious once you
have more than one service, and manually wiring up networking between them
is error-prone. This is exactly the problem **Docker Compose** solves.

### 7.1 Create `docker-compose.yml` at the **root** of the project

(i.e. next to the `01-web-app` and `02-rest-api` folders, NOT inside
either of them)

```yaml
services:

  web:
    build: ./01-web-app
    container_name: distsys-web
    ports:
      - "5000:5000"
    environment:
      - API_URL=http://api:5001
    depends_on:
      - api
    networks:
      - distsys-net

  api:
    build: ./02-rest-api
    container_name: distsys-api
    ports:
      - "5001:5001"
    networks:
      - distsys-net

networks:
  distsys-net:
    driver: bridge
```

**The single most important line to understand:** `API_URL=http://api:5001`.
Notice that `api` is not an IP address - it is literally the **service
name** defined above (`api:`). Docker Compose automatically creates a
private DNS entry for each service name inside the `distsys-net` network,
so the `web` container can reach the `api` container just by using its
service name as a hostname. This is service discovery, and it's the same
core idea used in real distributed systems and container orchestrators
like Kubernetes (which does the same thing at a larger scale).

### 7.2 Run everything

From the project root (where `docker-compose.yml` lives):

```bash
docker compose up --build
```

- `--build` forces Docker to (re)build both images from their Dockerfiles
  before starting. You only strictly need `--build` the first time, or
  after changing code - but it's a safe habit to always include it while
  learning.
- Leave this terminal window open; you'll see interleaved logs from both
  the `web` and `api` containers, each prefixed with its service name.

Open your browser to **http://localhost:5000**. You should now see:
- a hostname for the web container
- **"API status: connected"**
- a table of students, fetched live from the API container

This confirms two independent containers, each built from its own
Dockerfile, are successfully communicating over Docker's internal network.

### 7.3 Run in the background

If you don't want the logs taking over your terminal:

```bash
docker compose up --build -d
```

`-d` means "detached" (runs in the background). To view logs later:

```bash
docker compose logs -f
```

(`Ctrl + C` to stop watching logs - this does NOT stop the containers.)

To see what's running:

```bash
docker compose ps
```

To stop everything:

```bash
docker compose down
```

---

## 8. Part 5: Testing the REST API Directly

With `docker compose up` running, open a **new** terminal window and try
these (the API is reachable directly on your host at port 5001, because
of the `ports:` mapping in the compose file):

```bash
# List all students
curl http://localhost:5001/api/students

# Get one student
curl http://localhost:5001/api/students/1

# Create a new student (Mac/Linux terminal syntax)
curl -X POST http://localhost:5001/api/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Dwi Nugroho", "course": "Cloud Computing"}'
```

**On Windows PowerShell**, quoting works differently. Use this form
instead:

```powershell
curl -X POST http://localhost:5001/api/students `
  -H "Content-Type: application/json" `
  -d '{\"name\": \"Dwi Nugroho\", \"course\": \"Cloud Computing\"}'
```

Or, much easier on Windows: use **Postman** (`https://www.postman.com/`)
or the **Thunder Client** extension in VS Code, set the method to `POST`,
the URL to `http://localhost:5001/api/students`, the body type to JSON,
and paste:

```json
{ "name": "Dwi Nugroho", "course": "Cloud Computing" }
```

After creating a student, refresh `http://localhost:5000` in your browser
- the web app will show the new student too, because it fetches fresh
data from the API on every page load.

Try `DELETE` and `PUT` the same way, changing the HTTP method and, for
`PUT`, the fields you send.

---

## 9. Part 6: Distributed Systems Exercises

These exercises are the real point of the lab - use them in class or as
homework.

### 9.1 Inspect the network

```bash
docker network ls
docker network inspect docker-distsys-lab_distsys-net
```

Find the section listing both containers and their IP addresses inside
this private network. Notice they have real internal IPs, yet your code
never referenced an IP address - only the service name `api`. Discuss:
why is name-based discovery more robust than hard-coding IPs in a system
where containers can be destroyed and recreated at any time?

### 9.2 Look inside a running container

```bash
docker exec -it distsys-api /bin/bash
```

This opens a shell **inside** the running API container. From there, try:

```bash
hostname
ping web
cat /etc/hosts
exit
```

`ping web` demonstrates that the `api` container can also reach the `web`
container by name - the DNS resolution works both directions.

### 9.3 Scale the web service to multiple containers

```bash
docker compose up --build -d --scale web=3
```

Note: since `web` has a fixed host port (`5000:5000`) in the compose file,
running 3 replicas that all try to bind to the same host port will
conflict. To make scaling work cleanly, temporarily edit `docker-compose.yml`
and change the web service's ports to a range, e.g.:

```yaml
    ports:
      - "5000-5002:5000"
```

Re-run the scale command, then run:

```bash
docker compose ps
```

You'll see three `web` containers. Refresh `http://localhost:5000` (and
try `5001`, `5002`) a few times and note the **hostname** value shown on
the page changes depending on which container answered. Discuss: this is
the basic principle behind load balancing and horizontal scaling in
distributed systems - many identical, stateless workers behind one
address.

### 9.4 Observe what happens when a container "crashes"

```bash
docker kill distsys-api
docker compose ps
```

Refresh the web app in your browser - what does it show now? Then bring
the API back:

```bash
docker compose up -d api
```

Discuss: in this lab, the web app just shows an error when the API is
down. What would a more resilient distributed system do instead
(retries, timeouts, circuit breakers, fallback/cached data)?

### 9.5 State and persistence

Create a student via `POST`, then restart just the API container:

```bash
docker compose restart api
curl http://localhost:5001/api/students
```

The student you added is gone - the in-memory list was reset. Discuss:
where should state actually live in a distributed system so it survives
individual container restarts? (Answer directions: a database container
with a Docker **volume**, or an external managed database.) As a stretch
exercise, try adding a `volumes:` entry and a database service (e.g.
`postgres` or `redis`) to `docker-compose.yml` and connect the API to it.

### 9.6 Read the logs of a specific service

```bash
docker compose logs web
docker compose logs -f api
```

Notice each incoming HTTP request is logged with a timestamp, method, and
status code - the same kind of access log used to debug real distributed
systems.

---

## 10. Part 7: Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop isn't running. Launch it and wait for the whale icon to become idle. |
| `port is already allocated` | Something else on your computer is already using that port (5000 or 5001). Either stop that program, or change the left-hand number in `ports:` (e.g. `"5010:5000"`) and use that new port in your browser. |
| Browser shows "This site can't be reached" | Check the app uses `host="0.0.0.0"` (not `127.0.0.1`) inside the container, and that Docker Desktop is running. |
| `API status: could not reach API` even though `docker compose ps` shows both running | Give the API a few seconds to finish starting; or check `docker compose logs api` for a startup error (e.g. a typo in `app.py`). |
| Windows: paths with spaces cause errors | Avoid spaces in your project folder path, e.g. use `C:\Users\you\docker-distsys-lab` rather than a path containing `OneDrive - My University`. |
| Mac (Apple Silicon): a base image fails to pull or run oddly | `python:3.11-slim` used in this lab supports Apple Silicon natively, so this shouldn't happen here; if you later use a different image and hit this, add `platform: linux/amd64` under that service in the compose file as a workaround. |
| Changes to `app.py` don't show up | You need to rebuild: `docker compose up --build`. Docker does not automatically re-copy code into an image after it's built. |
| `docker compose` command not found | Older Docker versions used a separate `docker-compose` (with a hyphen) command. Update Docker Desktop, which bundles the newer `docker compose` (space) command. |

---

## 11. Part 8: Cleaning Up

Stop and remove the containers and network created by Compose:

```bash
docker compose down
```

Also remove the images built in this lab, to free disk space:

```bash
docker rmi web-app-image rest-api-image
docker compose down --rmi all
```

To see how much space Docker is using at any point:

```bash
docker system df
```

To remove ALL unused Docker data on your machine (images, containers,
networks not currently in use) - use with care, this affects other
projects too:

```bash
docker system prune
```

---

## 12. Part 9: What to Explore Next

Once comfortable with this lab, natural next steps for a distributed
systems course include:

- Add a **database** service (PostgreSQL or MongoDB) with a persistent
  **volume**, and connect the REST API to it instead of an in-memory list.
- Add a **third** service - for example a background worker or a second
  API - and practice wiring up a three-service system.
- Introduce a **reverse proxy / load balancer** (e.g. Nginx) in front of
  multiple `web` replicas.
- Explore **health checks** (`healthcheck:` in Compose) and restart
  policies (`restart: on-failure`).
- Compare this local Compose setup with a real orchestrator like
  **Kubernetes**, which automates scaling, service discovery, and
  self-healing across many physical machines instead of one laptop.

---

*End of hands-on guide.*
