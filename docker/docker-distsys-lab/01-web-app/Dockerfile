# --- Dockerfile for the WEB APP service ---
# This file tells Docker how to build an "image" (a snapshot/template)
# that can be run as a "container" (a running instance of that image).

# 1. Start from an official, lightweight Python image (the "base image")
FROM python:3.11-slim

# 2. Set the working directory INSIDE the container.
#    Every command below runs relative to this folder.
WORKDIR /app

# 3. Copy only the dependency list first (this makes rebuilds faster,
#    because Docker caches this layer if requirements.txt hasn't changed)
COPY requirements.txt .

# 4. Install the Python dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 5. Now copy the rest of the application code into the container
COPY . .

# 6. Document which port the app listens on (informational only)
EXPOSE 5000

# 7. The command that runs when the container starts
CMD ["python", "app.py"]
