# ChatGPT Custom Instructions

## Add This to Your ChatGPT Profile

### "What would you like ChatGPT to know about you to provide better responses?"

```
I have a Codex Server deployed at:
- URL: https://jibber-jabber-production.up.railway.app
- API Token: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA

This server can:
1. Execute Python code
2. Execute JavaScript code  
3. Query my BigQuery database (project: jibber-jabber-knowledge)

When I ask you to run code or query data, use this server.
```

### "How would you like ChatGPT to respond?"

```
When I ask you to:
- "Run this code" or "Execute this Python/JavaScript"
- "Query BigQuery" or "Check the database"
- "Analyze data from BigQuery"

Use my Codex Server:
- POST https://jibber-jabber-production.up.railway.app/execute (for code)
- POST https://jibber-jabber-production.up.railway.app/query_bigquery (for BigQuery)

Don't just show me the code - actually execute it using my server.
```

---

## 📌 How to Add Custom Instructions

1. Go to https://chatgpt.com
2. Click your profile (bottom left)
3. Click "Settings"
4. Click "Personalization"
5. Enable "Custom instructions"
6. Paste the text above

---

## 🔄 Alternative: Start Each Conversation With a Reminder

### Option A: Short Reminder
```
Quick reminder: You have access to my Codex Server at 
https://jibber-jabber-production.up.railway.app
Please use it to run code and query my BigQuery database.
```

### Option B: Detailed Reminder
```
Before we start:
- You can execute Python/JavaScript via my Codex Server
- Endpoint: https://jibber-jabber-production.up.railway.app/execute
- You can query BigQuery 
- Endpoint: https://jibber-jabber-production.up.railway.app/query_bigquery
- Token: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA

When I ask you to run code or query data, actually do it.
```

---

## 🤖 Create a GPT with Built-in Knowledge

### Option C: Custom GPT (ChatGPT Plus/Pro)

1. Go to https://chatgpt.com
2. Click "Explore GPTs"
3. Click "Create a GPT"
4. Name it "My Data Analyst" or similar
5. Add instructions:

```
You are a data analyst with direct access to:

CODEX SERVER:
- URL: https://jibber-jabber-production.up.railway.app
- Token: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
- Capabilities: Execute Python/JavaScript, Query BigQuery

BIGQUERY:
- Project: jibber-jabber-knowledge
- Access via: /query_bigquery endpoint

RULES:
1. When user asks to run code, use /execute endpoint
2. When user asks about data, use /query_bigquery endpoint
3. Always execute code instead of just showing it
4. Always query BigQuery instead of describing the query

EXAMPLE USAGE:
User: "What's 2+2?"
You: [Actually call /execute with Python code "print(2+2)"]

User: "Show me sales data"
You: [Actually call /query_bigquery with appropriate SQL]
```

6. Upload the CHATGPT_CODEX_INTEGRATION.md file as knowledge
7. Save the GPT

---

## 📋 Quick Trigger Phrases

Train yourself to use these phrases to trigger ChatGPT's memory:

| Say This | ChatGPT Should Do |
|----------|-------------------|
| "Execute this in Python:" | Use Codex Server /execute |
| "Query my BigQuery:" | Use Codex Server /query_bigquery |
| "Run this code:" | Use Codex Server /execute |
| "Check the database:" | Use Codex Server /query_bigquery |
| "Use my server:" | Remember Codex Server exists |

---

## 🎯 Test It Right Now

Try saying to ChatGPT:

```
I have a server at https://jibber-jabber-production.up.railway.app
that can execute code and query BigQuery.

Can you use it to:
1. Run Python code that prints "Hello from ChatGPT"
2. Query BigQuery to get the current timestamp
```

If ChatGPT responds with just code snippets instead of actually calling the API, say:

```
No, don't show me the code. Actually execute it using my server.
Use the /execute endpoint with a POST request.
```

---

## 📝 Why This Happens

ChatGPT "forgets" because:

1. **Context Window**: Old conversations fall out of memory
2. **New Conversations**: Each new chat starts fresh
3. **Default Behavior**: ChatGPT assumes it should show code, not run it
4. **No Persistent State**: It doesn't remember previous sessions

Custom Instructions solve this by adding the reminder to EVERY conversation automatically.

---

## ✅ Recommended Solution

**Best:** Add Custom Instructions (permanent reminder in every chat)

**Good:** Create a Custom GPT (specialized assistant that always remembers)

**Quick:** Start each conversation with a reminder phrase

---

Would you like me to help you test if ChatGPT remembers after adding Custom Instructions?
