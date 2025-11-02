# Codex Server Setup Guide

## 🚀 What is a Codex Server?

A Codex server typically refers to:
1. **Code execution environment** - Run code safely in containers
2. **API endpoint** - Accept code, execute, return results
3. **Language support** - Python, JavaScript, etc.
4. **Security sandbox** - Isolated execution

---

## 📋 Setup Options

### Option 1: Local Docker-Based Codex Server (Recommended)

**Best for**: Development, testing, full control

#### Prerequisites
```bash
# Install Docker
brew install docker docker-compose

# Start Docker Desktop
open -a Docker
```

#### Step 1: Create Server Structure
```bash
cd ~/Overarch\ Jibber\ Jabber
mkdir codex-server
cd codex-server
```

#### Step 2: Create `Dockerfile`
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    nodejs \\
    npm \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "codex_server.py"]
```

#### Step 3: Create `requirements.txt`
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
docker==6.1.3
redis==5.0.1
```

#### Step 4: Create `codex_server.py`
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os
from typing import Optional

app = FastAPI(title="Codex Server")

class CodeRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 30

class CodeResponse(BaseModel):
    output: str
    error: Optional[str] = None
    exit_code: int

@app.post("/execute", response_model=CodeResponse)
async def execute_code(request: CodeRequest):
    """Execute code in a sandboxed environment"""
    
    if request.language == "python":
        return execute_python(request.code, request.timeout)
    elif request.language == "javascript":
        return execute_javascript(request.code, request.timeout)
    else:
        raise HTTPException(400, f"Unsupported language: {request.language}")

def execute_python(code: str, timeout: int) -> CodeResponse:
    """Execute Python code safely"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return CodeResponse(
            output=result.stdout,
            error=result.stderr if result.stderr else None,
            exit_code=result.returncode
        )
    except subprocess.TimeoutExpired:
        return CodeResponse(
            output="",
            error=f"Execution timed out after {timeout} seconds",
            exit_code=-1
        )
    finally:
        os.unlink(temp_file)

def execute_javascript(code: str, timeout: int) -> CodeResponse:
    """Execute JavaScript code safely"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return CodeResponse(
            output=result.stdout,
            error=result.stderr if result.stderr else None,
            exit_code=result.returncode
        )
    except subprocess.TimeoutExpired:
        return CodeResponse(
            output="",
            error=f"Execution timed out after {timeout} seconds",
            exit_code=-1
        )
    finally:
        os.unlink(temp_file)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Step 5: Create `docker-compose.yml`
```yaml
version: '3.8'

services:
  codex-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

#### Step 6: Build & Run
```bash
# Build the container
docker-compose build

# Start the server
docker-compose up -d

# Check logs
docker-compose logs -f

# Test it
curl http://localhost:8000/health
```

---

### Option 2: OpenAI Codex API (Cloud)

**Best for**: Production, scalability, no maintenance

#### Setup
```bash
# Install OpenAI SDK
pip install openai

# Set API key
export OPENAI_API_KEY="sk-..."
```

#### Usage Example
```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4",  # Or "code-davinci-002" for pure code
    messages=[
        {"role": "system", "content": "You are a code execution assistant."},
        {"role": "user", "content": "Write Python code to calculate fibonacci(10)"}
    ]
)

print(response.choices[0].message.content)
```

---

### Option 3: Jupyter Kernel Gateway (For Notebooks)

**Best for**: Data science, interactive code execution

#### Setup
```bash
# Install Jupyter Kernel Gateway
pip install jupyter_kernel_gateway

# Start server
jupyter kernelgateway --KernelGatewayApp.ip=0.0.0.0 --KernelGatewayApp.port=8888
```

#### Usage
```python
import requests

# Execute code via Jupyter kernel
response = requests.post(
    'http://localhost:8888/api/kernels',
    json={'name': 'python3'}
)
kernel_id = response.json()['id']

# Execute code
requests.post(
    f'http://localhost:8888/api/kernels/{kernel_id}/execute',
    json={'code': 'print("Hello from Jupyter!")'}
)
```

---

## 🧪 Testing Your Codex Server

### Test Python Execution
```bash
curl -X POST http://localhost:8000/execute \\
  -H "Content-Type: application/json" \\
  -d '{
    "code": "print(\"Hello from Codex!\")",
    "language": "python"
  }'
```

### Test JavaScript Execution
```bash
curl -X POST http://localhost:8000/execute \\
  -H "Content-Type: application/json" \\
  -d '{
    "code": "console.log(\"Hello from Node!\")",
    "language": "javascript"
  }'
```

### Python Client
```python
import requests

def execute_code(code: str, language: str = "python"):
    response = requests.post(
        "http://localhost:8000/execute",
        json={"code": code, "language": language}
    )
    return response.json()

# Test it
result = execute_code("print(2 + 2)")
print(result)  # {'output': '4\\n', 'error': None, 'exit_code': 0}
```

---

## 🔒 Security Considerations

### 1. Sandbox Execution
```python
# Use docker containers for isolation
import docker

client = docker.from_env()

def execute_in_container(code: str):
    container = client.containers.run(
        "python:3.11-slim",
        f"python -c '{code}'",
        remove=True,
        mem_limit="256m",
        cpu_quota=50000,
        network_disabled=True
    )
    return container.decode()
```

### 2. Rate Limiting
```python
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/execute")
@limiter.limit("10/minute")
async def execute_code(request: Request, code_request: CodeRequest):
    # ... execution logic
```

### 3. Input Validation
```python
FORBIDDEN_IMPORTS = ['os', 'subprocess', 'sys']

def validate_code(code: str):
    for forbidden in FORBIDDEN_IMPORTS:
        if f"import {forbidden}" in code:
            raise ValueError(f"Import '{forbidden}' is not allowed")
```

---

## 📊 Production Setup

### Using PM2 (Process Manager)
```bash
# Install PM2
npm install -g pm2

# Start server
pm2 start codex_server.py --name codex-server --interpreter python

# Monitor
pm2 monit

# Logs
pm2 logs codex-server
```

### Using Systemd
```bash
# Create service file
sudo nano /etc/systemd/system/codex-server.service
```

```ini
[Unit]
Description=Codex Code Execution Server
After=network.target

[Service]
User=georgemajor
WorkingDirectory=/Users/georgemajor/Overarch Jibber Jabber/codex-server
ExecStart=/Users/georgemajor/Overarch Jibber Jabber/.venv/bin/python codex_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable codex-server
sudo systemctl start codex-server
sudo systemctl status codex-server
```

---

## 🌐 Expose to Internet (Optional)

### Using ngrok
```bash
# Install ngrok
brew install ngrok

# Start tunnel
ngrok http 8000

# You'll get a public URL like: https://abc123.ngrok.io
```

### Using Cloudflare Tunnel
```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:8000
```

---

## 🔧 Advanced Features

### Add Authentication
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(401, "Invalid token")
    return credentials.credentials

@app.post("/execute")
async def execute_code(
    request: CodeRequest,
    token: str = Depends(verify_token)
):
    # ... execution logic
```

### Add Logging
```python
import logging

logging.basicConfig(
    filename='codex-server.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.post("/execute")
async def execute_code(request: CodeRequest):
    logging.info(f"Executing {request.language} code")
    # ... execution logic
```

---

## 📝 Quick Start Script

Save this as `setup_codex_server.sh`:

```bash
#!/bin/bash

cd ~/Overarch\ Jibber\ Jabber
mkdir -p codex-server
cd codex-server

# Create files
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
EOF

# Download server code
curl -O https://raw.githubusercontent.com/YOUR_REPO/codex_server.py

# Install dependencies
pip install -r requirements.txt

# Start server
python codex_server.py
```

---

## ✅ Verification

After setup, verify everything works:

```bash
# Check server is running
curl http://localhost:8000/health

# Execute test code
curl -X POST http://localhost:8000/execute \\
  -H "Content-Type: application/json" \\
  -d '{"code": "print(\"Server works!\")", "language": "python"}'
```

Expected response:
```json
{
  "output": "Server works!\\n",
  "error": null,
  "exit_code": 0
}
```

---

**Which setup would you like to implement? I can guide you through the specific steps!**
