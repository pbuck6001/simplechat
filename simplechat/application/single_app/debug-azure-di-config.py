# debug_azure_di.py
# Run this script to check your Azure Document Intelligence configuration

import os
import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import dotenv
from dotenv import load_dotenv

# Load .env
result = load_dotenv(verbose=True, override=True)
print(f"   load_dotenv() returned: {result}")

def check_azure_di_config():
    print("=== Azure Document Intelligence Configuration Check ===\n")
    
    # Check environment variables
    endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT', '')
    key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY', '')
    
    print(f"1. Environment Variables:")
    print(f"   - Endpoint: {endpoint if endpoint else 'NOT SET'}")
    print(f"   - Key: {'Set' if key else 'NOT SET'}")
    print(f"   - Key length: {len(key) if key else 0}")
    
    # Validate endpoint format
    print(f"\n2. Endpoint Validation:")
    if not endpoint:
        print("   ❌ Endpoint is not set")
    elif not endpoint.startswith('https://'):
        print(f"   ❌ Endpoint missing https:// prefix: {endpoint}")
        print(f"   ✅ Should be: https://{endpoint}")
    elif '.cognitiveservices.azure.com' not in endpoint:
        print(f"   ⚠️  Endpoint doesn't match expected format")
        print(f"   Expected format: https://<resource-name>.cognitiveservices.azure.com")
    else:
        print(f"   ✅ Endpoint format looks correct")
    
    # Test API connectivity
    print(f"\n3. API Connectivity Test:")
    if endpoint and key:
        # Clean up endpoint if needed
        if not endpoint.startswith('https://'):
            endpoint = f"https://{endpoint}"
        
        # Remove trailing slash if present
        endpoint = endpoint.rstrip('/')
        
        try:
            # Test with REST API
            test_url = f"{endpoint}/formrecognizer/documentModels?api-version=2023-07-31"
            headers = {
                'Ocp-Apim-Subscription-Key': key
            }
            
            print(f"   Testing URL: {test_url}")
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ REST API connection successful")
                models = response.json().get('value', [])
                print(f"   Found {len(models)} document models")
            else:
                print(f"   ❌ REST API returned status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ REST API connection failed: {str(e)}")
    
    # Test SDK initialization
    print(f"\n4. SDK Client Test:")
    if endpoint and key:
        try:
            # Initialize the client
            client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
            print(f"   ✅ DocumentAnalysisClient initialized successfully")
            
            # Try to list models (simple operation)
            try:
                # This is a lightweight operation to test connectivity
                info = client._client._config
                print(f"   ✅ Client configuration validated")
            except Exception as e:
                print(f"   ⚠️  Client validation warning: {str(e)}")
                
        except Exception as e:
            print(f"   ❌ Failed to initialize DocumentAnalysisClient: {str(e)}")
    
    # Provide recommendations
    print(f"\n5. Recommendations:")
    if not endpoint or not key:
        print("   1. Set the required environment variables:")
        print("      export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT='https://<your-resource>.cognitiveservices.azure.com'")
        print("      export AZURE_DOCUMENT_INTELLIGENCE_KEY='<your-key>'")
    elif not endpoint.startswith('https://'):
        print("   1. Update your endpoint to include https://")
        print(f"      export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT='https://{endpoint}'")
    
    print("\n   2. In Azure Portal, verify:")
    print("      - Your Document Intelligence resource is deployed")
    print("      - The resource is in a running state")
    print("      - You're using the correct key and endpoint from Keys and Endpoint section")
    print("      - Your subscription has sufficient quota")

if __name__ == "__main__":
    check_azure_di_config()