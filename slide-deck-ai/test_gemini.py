#!/usr/bin/env python3
"""
Test Gemini API connection and basic functionality
"""

import os
import json
import requests
from dotenv import load_dotenv

def test_gemini_api():
    """Test if Gemini API is working with our setup"""
    load_dotenv()
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Simple test prompt
    prompt = """Create a simple JSON with title and 3 bullet points:
    {"title": "Test Title", "points": ["Point 1", "Point 2", "Point 3"]}"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "candidateCount": 1,
            "maxOutputTokens": 1000
        }
    }
    
    try:
        print("🤖 Testing Gemini API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['candidates'][0]['content']['parts'][0]['text']
        
        print("✅ Gemini API is working!")
        print(f"📝 Response: {content[:200]}...")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except KeyError as e:
        print(f"❌ API response format error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Gemini API Setup")
    print("=" * 30)
    
    success = test_gemini_api()
    
    if success:
        print("\\n🎉 Setup is working! You can now use the Gemini-based tools.")
    else:
        print("\\n❌ Setup needs fixing. Please check your API key and internet connection.")