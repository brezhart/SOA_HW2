FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate Python code from protobuf
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. post.proto

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
