#!/usr/bin/env python3
"""
Create OpenAI Assistant: Dashboard Jibber Jabber
Automatically sets up an Assistant with project knowledge and instructions
"""

import os
import sys
import time
from openai import OpenAI

# ---- Configuration ----
MODEL = "gpt-4-1106-preview"  # or "gpt-4-turbo-preview" or your preferred model

INSTRUCTIONS = """
Project Configuration — Dashboard Jibber Jabber

BigQuery
- Project ID: inner-cinema-476211-u9
- Datasets: uk_energy_prod, companies_house
- Railway API: https://jibber-jabber-production.up.railway.app

Usage rules
- Use bmrs_indgen_iris for total GB gen (boundary='N'); no fuelType in this table
- Use bmrs_fuelinst_iris for fuel-type breakdowns incl. interconnectors
- Check INFORMATION_SCHEMA before creating views
- Prefer SQL or pure Python (no pandas/numpy on Railway)

System Status (2025-11-08)
- Railway backend: ✅ Working (BigQuery access verified: 155,405 rows)
- Vercel proxy: ✅ Working (full chain tested)
- Apps Script: ✅ Deployed (Enhanced Dashboard v2 with chart creation)
- Google Sheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

Architecture
- Apps Script → Vercel Proxy → Railway Backend → BigQuery (inner-cinema-476211-u9)
"""

FILE_PATH = "COPY_PASTE_TO_CHATGPT_CORRECTED.md"

def main():
    print("🤖 Creating OpenAI Assistant: Dashboard Jibber Jabber\n")
    
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("\nPlease set your API key:")
        print("   export OPENAI_API_KEY='sk-...'")
        print("\nOr create a .env file with:")
        print("   OPENAI_API_KEY=sk-...")
        return False
    
    client = OpenAI(api_key=api_key)
    
    # Check if file exists
    if not os.path.exists(FILE_PATH):
        print(f"⚠️  Warning: {FILE_PATH} not found")
        print("   Creating assistant without knowledge file...")
        file_id = None
        vs_id = None
    else:
        print(f"📁 Uploading knowledge file: {FILE_PATH}")
        try:
            # 1) Upload file
            with open(FILE_PATH, "rb") as f:
                file = client.files.create(file=f, purpose="assistants")
            file_id = file.id
            print(f"   ✅ File uploaded: {file_id}")
            
            # 2) Create vector store
            print(f"\n📚 Creating vector store...")
            vs = client.beta.vector_stores.create(name="JibberJabber-KB")
            vs_id = vs.id
            print(f"   ✅ Vector store created: {vs_id}")
            
            # 3) Add file to vector store
            print(f"\n🔗 Attaching file to vector store...")
            client.beta.vector_stores.files.create(
                vector_store_id=vs_id,
                file_id=file_id
            )
            print(f"   ✅ File attached to vector store")
            
        except Exception as e:
            print(f"   ❌ Error with file: {e}")
            print("   Creating assistant without file...")
            file_id = None
            vs_id = None
    
    # 3) Create the Assistant
    print(f"\n🤖 Creating Assistant...")
    try:
        assistant_config = {
            "name": "Dashboard Jibber Jabber",
            "model": MODEL,
            "instructions": INSTRUCTIONS,
            "tools": [{"type": "code_interpreter"}]
        }
        
        # Add file search if we have a vector store
        if vs_id:
            assistant_config["tools"].append({"type": "file_search"})
            assistant_config["tool_resources"] = {
                "file_search": {"vector_store_ids": [vs_id]}
            }
        
        assistant = client.beta.assistants.create(**assistant_config)
        
        print(f"   ✅ Assistant created: {assistant.id}")
        print(f"\n📋 Assistant Details:")
        print(f"   Name: {assistant.name}")
        print(f"   Model: {assistant.model}")
        print(f"   ID: {assistant.id}")
        if vs_id:
            print(f"   Vector Store: {vs_id}")
        if file_id:
            print(f"   Knowledge File: {file_id}")
        
    except Exception as e:
        print(f"   ❌ Error creating assistant: {e}")
        return False
    
    # 4) Quick smoke test
    print(f"\n🧪 Running smoke test...")
    try:
        thread = client.beta.threads.create(
            messages=[{
                "role": "user",
                "content": "Which BigQuery project should I use and which table has fuelType?"
            }]
        )
        print(f"   ✅ Thread created: {thread.id}")
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        print(f"   ✅ Run started: {run.id}")
        
        # Wait for completion
        print(f"   ⏳ Waiting for response...")
        max_wait = 30
        waited = 0
        while waited < max_wait:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                print(f"   ✅ Run completed!")
                
                # Get the response
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                if messages.data:
                    response = messages.data[0].content[0].text.value
                    print(f"\n💬 Assistant Response:")
                    print(f"   {response[:200]}...")
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                print(f"   ❌ Run {run_status.status}")
                break
            
            time.sleep(2)
            waited += 2
        
        if waited >= max_wait:
            print(f"   ⏰ Timeout waiting for response")
        
    except Exception as e:
        print(f"   ❌ Smoke test error: {e}")
    
    # Summary
    print(f"\n" + "="*60)
    print(f"✅ Assistant Setup Complete!")
    print(f"="*60)
    print(f"\n📝 Save these IDs:")
    print(f"   Assistant ID: {assistant.id}")
    if vs_id:
        print(f"   Vector Store ID: {vs_id}")
    if file_id:
        print(f"   File ID: {file_id}")
    
    print(f"\n🔗 Next Steps:")
    print(f"   1. Go to: https://platform.openai.com/assistants")
    print(f"   2. Find: 'Dashboard Jibber Jabber'")
    print(f"   3. Test queries about your BigQuery setup")
    
    print(f"\n💡 Example queries to try:")
    print(f"   • Which BigQuery project should I use?")
    print(f"   • What's the Railway API endpoint?")
    print(f"   • Which table has fuel type breakdowns?")
    print(f"   • Show me the system architecture")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
