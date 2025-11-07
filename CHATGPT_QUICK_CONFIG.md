# 🎯 ChatGPT Action - Quick Configuration Card

**Time**: 10 minutes  
**Guide**: DEPLOYMENT_SUCCESS_CHATGPT_SETUP.md  

---

## Quick Steps:

### 1️⃣ Go to ChatGPT Actions
```
https://chatgpt.com/ → Settings → Personalization → Custom Actions → Create new action
```

### 2️⃣ Action Details
```
Name: GB Power Market API
Description: Access UK electricity market data and server management
```

### 3️⃣ Schema
```
Open: chatgpt-action-schema.json
Copy ALL contents (555 lines)
Paste into Schema field
```

### 4️⃣ Authentication
```
Type: API Key
Header Name: Authorization
Format: Bearer {api_key}
API Key: 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af
```

### 5️⃣ Server URL
```
http://94.237.55.15:8000
```

### 6️⃣ Save & Test
```
Test prompt: "Check the status of my Power Market API"
```

---

## Expected Result:

ChatGPT will call your API and respond with:
- Server version: 3.0.0
- Status: healthy
- Available features
- Component health

---

## Test Prompts:

```
✅ "What version is my GB Power Market API running?"
✅ "Check my Power Market API status"
✅ "Is my Power Market server healthy?"
```

---

## 🎉 That's it!

Once configured, ChatGPT can directly query your infrastructure!

**Full Guide**: DEPLOYMENT_SUCCESS_CHATGPT_SETUP.md
