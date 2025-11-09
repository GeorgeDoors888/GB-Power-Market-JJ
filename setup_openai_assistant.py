#!/usr/bin/env python3
"""
Create OpenAI Assistant for Dashboard Jibber Jabber
Uploads documentation and sets up File Search for context-aware responses
"""

import os
import sys
from pathlib import Path

# Check if openai is installed
try:
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI package not installed!")
    print("\n📦 Install with:")
    print("   pip3 install openai python-dotenv")
    print("\nOr try:")
    print("   python3 -m pip install openai python-dotenv")
    sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, trying to use environment variables directly...")

# Configuration
MODEL = "gpt-4o-mini"  # ChatGPT model
INSTRUCTIONS = """
Project Configuration — Dashboard Jibber Jabber

BigQuery
- Project ID: inner-cinema-476211-u9
- Datasets: uk_energy_prod, companies_house
- Railway API: https://jibber-jabber-production.up.railway.app
- Bearer Token: Available in environment as BEARER_TOKEN

Usage rules
- Use bmrs_indgen_iris for total GB gen (boundary='N'); no fuelType in this table
- Use bmrs_fuelinst_iris for fuel-type breakdowns incl. interconnectors
- Check INFORMATION_SCHEMA before creating views
- Prefer SQL or pure Python (no pandas/numpy on Railway)

API Security
- Railway API requires: Authorization: Bearer {BEARER_TOKEN}
- Never expose the token in responses
- Use environment variables for sensitive data

Key Tables:
- bmrs_mid: System prices (SSP, SBP)
- bmrs_bod: Bid-Offer Data
- bmrs_boalf: BOALF acceptances
- bmrs_indgen_iris: Individual generator data
- bmrs_inddem_iris: Demand data
- bmrs_fuelinst_iris: Fuel type breakdown with interconnectors
"""

def check_openai_key():
    """Check if OPENAI_API_KEY is set"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'sk-your-key-here':
        print("❌ OPENAI_API_KEY not set!")
        print("\n📝 Please:")
        print("1. Get your API key from: https://platform.openai.com/api-keys")
        print("2. Add it to .env file:")
        print("   OPENAI_API_KEY=sk-your-actual-key-here")
        print("\n3. Or export it:")
        print("   export OPENAI_API_KEY=sk-your-actual-key-here")
        return False
    return True

def find_corrected_doc():
    """Find the corrected documentation file"""
    possible_names = [
        "COPY_PASTE_TO_CHATGPT_CORRECTED.md",
        "COPY_PASTE_TO_CHATGPT.md",
        "PROJECT_IDENTITY_MASTER.md",
        "RAILWAY_BIGQUERY_FIX_STATUS.md"
    ]
    
    for name in possible_names:
        if os.path.exists(name):
            return name
    
    # If not found, list available .md files
    md_files = list(Path('.').glob('*.md'))
    if md_files:
        print("\n📄 Available documentation files:")
        for i, f in enumerate(md_files[:10], 1):
            print(f"   {i}. {f.name}")
        return None
    
    return None

def create_assistant():
    """Create the OpenAI Assistant with file search"""
    
    print("🤖 Creating OpenAI Assistant: Dashboard Jibber Jabber\n")
    
    # Check API key
    if not check_openai_key():
        return False
    
    # Find documentation file
    doc_file = find_corrected_doc()
    if not doc_file:
        print("\n⚠️  No documentation file found!")
        print("Using just instructions without file upload.")
        doc_file = None
    else:
        print(f"📄 Found documentation: {doc_file}")
    
    try:
        # Initialize OpenAI client
        client = OpenAI()
        
        # Upload documentation file if found
        if doc_file:
            print(f"\n📤 Uploading {doc_file}...")
            with open(doc_file, "rb") as f:
                file_obj = client.files.create(file=f, purpose="assistants")
            print(f"✅ File uploaded: {file_obj.id}")
            
            # Create vector store
            print("\n🗄️  Creating vector store...")
            vs = client.vector_stores.create(name="JibberJabber-KB")
            print(f"✅ Vector store created: {vs.id}")
            
            # Add file to vector store
            print(f"\n🔗 Attaching file to vector store...")
            client.vector_stores.files.create(
                vector_store_id=vs.id, 
                file_id=file_obj.id
            )
            print(f"✅ File attached to vector store")
            
            # Create assistant with file search
            print("\n🤖 Creating assistant with file search...")
            assistant = client.assistants.create(
                name="Dashboard Jibber Jabber",
                model=MODEL,
                instructions=INSTRUCTIONS,
                tool_resources={"file_search": {"vector_store_ids": [vs.id]}},
                tools=[{"type": "file_search"}]
            )
        else:
            # Create assistant without file search
            print("\n🤖 Creating assistant...")
            assistant = client.assistants.create(
                name="Dashboard Jibber Jabber",
                model=MODEL,
                instructions=INSTRUCTIONS
            )
        
        print(f"✅ Assistant created: {assistant.id}")
        
        # Test the assistant
        print("\n🧪 Running smoke test...")
        thread = client.threads.create(
            messages=[{
                "role": "user",
                "content": "Which BigQuery project should I use and which table has fuelType?"
            }]
        )
        print(f"✅ Thread created: {thread.id}")
        
        run = client.threads.runs.create(
            thread_id=thread.id, 
            assistant_id=assistant.id
        )
        print(f"✅ Run started: {run.id}")
        
        # Wait for completion
        print("\n⏳ Waiting for response...")
        import time
        while run.status in ["queued", "in_progress"]:
            time.sleep(1)
            run = client.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        if run.status == "completed":
            # Get messages
            messages = client.threads.messages.list(thread_id=thread.id)
            last_message = messages.data[0]
            print("\n✅ Test Response:")
            print("-" * 60)
            print(last_message.content[0].text.value)
            print("-" * 60)
        else:
            print(f"\n⚠️  Run status: {run.status}")
        
        # Save assistant ID
        print("\n💾 Saving assistant configuration...")
        with open('.env', 'a') as f:
            f.write(f"\n# OpenAI Assistant\n")
            f.write(f"OPENAI_ASSISTANT_ID={assistant.id}\n")
            if doc_file:
                f.write(f"OPENAI_VECTOR_STORE_ID={vs.id}\n")
        
        print("\n🎉 Success! Your assistant is ready.")
        print("\n📋 Summary:")
        print(f"   Assistant ID: {assistant.id}")
        if doc_file:
            print(f"   Vector Store: {vs.id}")
            print(f"   File: {file_obj.id} ({doc_file})")
        print(f"   Model: {MODEL}")
        
        print("\n🔗 Manage your assistant:")
        print("   https://platform.openai.com/assistants")
        
        print("\n💡 Next steps:")
        print("   1. Test in OpenAI Playground")
        print("   2. Integrate with your ChatGPT project")
        print("   3. Use the assistant ID in your API calls")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = create_assistant()
    sys.exit(0 if success else 1)
