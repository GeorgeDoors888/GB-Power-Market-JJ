# Connecting ChatGPT to Your Codex Server

## 🔐 **Authentication Options**

Your Codex server is currently **open** (no authentication). Here's how to add security and connect ChatGPT:

---

## 🚀 **Quick Setup: Make Port Public**

### Step 1: Make Your Server Publicly Accessible

In your Codespace:
1. Click **"PORTS"** tab (bottom panel)
2. Right-click on port **8000**
3. Select **"Port Visibility: Public"**
4. Copy the URL (e.g., `https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev`)

**⚠️ Warning:** This makes your server accessible to anyone with the URL!

---

## 🔒 **Option A: Add Token Authentication (Recommended)**

### Update Your Server with Authentication:

Add this to `codex_server.py`:

```python
from fastapi import Header, HTTPException
import secrets

# Generate a secret token (save this!)
SECRET_TOKEN = "codex_" + secrets.token_urlsafe(32)
print(f"🔑 Your API Token: {SECRET_TOKEN}")
print("Save this token - you'll need it for ChatGPT!")

@app.post("/execute", response_model=CodeResponse)
async def execute_code(
    request: CodeRequest,
    authorization: str = Header(None)
):
    """Execute code with authentication"""
    
    # Verify token
    if not authorization or authorization != f"Bearer {SECRET_TOKEN}":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Include 'Authorization: Bearer YOUR_TOKEN' header"
        )
    
    # Validate code
    validate_code(request.code, request.language)
    
    # Execute
    if request.language == "python":
        return execute_python(request.code, request.timeout)
    elif request.language == "javascript":
        return execute_javascript(request.code, request.timeout)
```

### Then Give ChatGPT the Token:

```
ChatGPT, my code execution server requires authentication:
URL: https://[your-url]/execute
Token: Bearer codex_abc123...
Please include the token in the Authorization header when making requests.
```

---

## 📋 **Option B: ChatGPT Custom Action (Best Integration)**

### Step 1: Create OpenAPI Schema

Save this as `openapi.yaml`:

```yaml
openapi: 3.0.0
info:
  title: Codex Code Execution Server
  description: Execute Python and JavaScript code safely
  version: 1.0.0
servers:
  - url: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev
    description: GitHub Codespace

paths:
  /health:
    get:
      summary: Health check
      responses:
        '200':
          description: Server is healthy
          
  /execute:
    post:
      summary: Execute code
      description: Execute Python or JavaScript code with timeout
      operationId: executeCode
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - code
                - language
              properties:
                code:
                  type: string
                  description: The code to execute
                  example: "print('Hello World')"
                language:
                  type: string
                  enum: [python, javascript]
                  description: Programming language
                  default: python
                timeout:
                  type: integer
                  description: Execution timeout in seconds
                  default: 10
                  minimum: 1
                  maximum: 30
      responses:
        '200':
          description: Code executed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  output:
                    type: string
                    description: Standard output from execution
                  error:
                    type: string
                    description: Error output if any
                  exit_code:
                    type: integer
                    description: Process exit code
                  execution_time:
                    type: number
                    description: Execution time in seconds
                  timestamp:
                    type: string
                    description: Execution timestamp
        '400':
          description: Bad request (invalid code or language)
        '500':
          description: Execution error

  /languages:
    get:
      summary: List supported languages
      responses:
        '200':
          description: List of supported languages
          content:
            application/json:
              schema:
                type: object
                properties:
                  languages:
                    type: array
                    items:
                      type: object
                      properties:
                        name:
                          type: string
                        version:
                          type: string
                        available:
                          type: boolean

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      
# Uncomment if you add authentication:
# security:
#   - BearerAuth: []
```

### Step 2: Configure in ChatGPT

1. Go to **ChatGPT Settings**
2. Navigate to **"GPTs"** or **"Actions"**
3. Click **"Create a GPT"** or **"Add Action"**
4. Paste the OpenAPI schema above
5. Test the connection
6. Save

### Step 3: Use in ChatGPT

Now you can say:
```
"Execute this Python code: print('Hello from ChatGPT!')"
"Run this JavaScript: console.log(2 + 2)"
```

ChatGPT will automatically call your Codex server!

---

## 🌐 **Option C: Use Webhook/Zapier (No Code)**

If you don't want to mess with APIs:

1. Use **Zapier** or **Make.com** to create a webhook
2. Webhook receives ChatGPT requests
3. Forwards to your Codex server
4. Returns results to ChatGPT

---

## 🔐 **Security Best Practices**

### If You Make Port Public:

1. **Add Authentication** (Bearer token recommended)
2. **Add Rate Limiting:**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=lambda: "global")
   
   @app.post("/execute")
   @limiter.limit("10/minute")
   async def execute_code(request: CodeRequest):
       # ... your code
   ```

3. **Monitor Logs:**
   ```python
   import logging
   logging.info(f"Request from: {request.headers.get('user-agent')}")
   ```

4. **Set Short Expiry:**
   - Codespace auto-stops after 30min (already configured ✅)
   - Delete Codespace when not in use

---

## 📱 **Current Setup (What You Have)**

```
Your Mac → Codespace (GitHub Cloud) → Codex Server
                                          ↑
                                          Port 8000
                                          Private (needs to be made public)
```

### To Allow ChatGPT Access:

```
ChatGPT → Public URL → Codespace → Codex Server
         (https://[url]-8000.app.github.dev)
```

---

## ✅ **Quick Start Checklist**

- [ ] Make port 8000 public in Codespaces PORTS tab
- [ ] Copy the public URL
- [ ] (Optional) Add authentication to codex_server.py
- [ ] Test with curl: `curl https://[your-url]/health`
- [ ] Share URL with ChatGPT or create Custom Action
- [ ] Test code execution through ChatGPT

---

## 🧪 **Test Commands**

### Test Publicly:
```bash
# From your Mac terminal (not Codespace)
curl https://[your-codespace-url]/health

curl -X POST https://[your-codespace-url]/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(2+2)", "language": "python"}'
```

### Tell ChatGPT:
```
My code execution server is at:
https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev

Please execute this Python code:
print("Hello from ChatGPT!")
```

---

## ❓ **FAQ**

**Q: Is my Codespace URL permanent?**
A: No, it changes if you delete and recreate the Codespace. Use a stable deployment (Railway) for permanent URLs.

**Q: Will ChatGPT automatically know about my server?**
A: No, you need to either:
   - Create a Custom Action with the OpenAPI schema
   - Or tell ChatGPT the URL in each conversation

**Q: Is it safe to make port public?**
A: Without authentication, anyone can execute code. Add Bearer token authentication for security.

**Q: How much does this cost?**
A: Codespace: FREE for 60 hours/month. After that: $0.18/hour for 2-core machine.

**Q: Can I use this from my phone?**
A: Yes! ChatGPT mobile app can call the public URL just like desktop.

---

**Next Step: Make port 8000 public in your Codespace PORTS tab, then test the URL!**
