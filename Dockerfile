# Start from an official small Python image
FROM python:3.12-slim

# Work inside /app in the container
WORKDIR /app

# Install the Python libraries first (cached between builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our code into the container
COPY app/ .

# Start the web server on port 8765
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]
