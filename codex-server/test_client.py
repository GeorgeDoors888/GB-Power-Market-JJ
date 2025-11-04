#!/usr/bin/env python3
"""
Codex Server Test Client
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()

def test_python_execution():
    """Test Python code execution"""
    print("🐍 Testing Python execution...")
    
    code = """
print("Hello from Python!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
    
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "code": code,
            "language": "python",
            "timeout": 30
        }
    )
    
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Output: {result['output']}")
    print(f"   Exit code: {result['exit_code']}")
    print(f"   Execution time: {result['execution_time']}s")
    print()

def test_javascript_execution():
    """Test JavaScript code execution"""
    print("📜 Testing JavaScript execution...")
    
    code = """
console.log("Hello from JavaScript!");
const result = 2 + 2;
console.log(`2 + 2 = ${result}`);
"""
    
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "code": code,
            "language": "javascript",
            "timeout": 30
        }
    )
    
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Output: {result['output']}")
    print(f"   Exit code: {result['exit_code']}")
    print(f"   Execution time: {result['execution_time']}s")
    print()

def test_error_handling():
    """Test error handling"""
    print("❌ Testing error handling...")
    
    code = "print(undefined_variable)"
    
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "code": code,
            "language": "python"
        }
    )
    
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Error: {result['error'][:100] if result['error'] else 'None'}")
    print(f"   Exit code: {result['exit_code']}")
    print()

def test_languages():
    """Test languages endpoint"""
    print("🌍 Testing languages endpoint...")
    response = requests.get(f"{BASE_URL}/languages")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Codex Server Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_python_execution()
        test_javascript_execution()
        test_error_handling()
        test_languages()
        
        print("✅ All tests completed!")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server at", BASE_URL)
        print("   Make sure the server is running:")
        print("   cd codex-server && python codex_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")
