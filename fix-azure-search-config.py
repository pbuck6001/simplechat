# debug_and_fix_azure_search.py
# Script to debug and fix Azure Search configuration issues

import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
import dotenv

# Load .env
result = dotenv.load_dotenv(verbose=True, override=True)
print(f"   load_dotenv() returned: {result}")

def check_search_config():
    print("=== Azure Cognitive Search Configuration Check ===\n")
    
    # Check environment variables
    search_endpoint = os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT', '')
    search_key = os.getenv('AZURE_SEARCH_ADMIN_KEY', '')
    
    # Alternative env var names that might be used
    if not search_endpoint:
        search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT', '')
    if not search_key:
        search_key = os.getenv('AZURE_SEARCH_KEY', '')
    
    print(f"1. Environment Variables:")
    print(f"   - Search Endpoint: {search_endpoint if search_endpoint else 'NOT SET'}")
    print(f"   - Search Key: {'Set' if search_key else 'NOT SET'}")
    
    # Validate endpoint format
    print(f"\n2. Endpoint Validation:")
    if not search_endpoint:
        print("   ❌ Search endpoint is not set")
    elif not search_endpoint.startswith('https://'):
        print(f"   ❌ Endpoint missing https:// prefix: {search_endpoint}")
        print(f"   ✅ Should be: https://{search_endpoint}")
    elif '.search.windows.net' not in search_endpoint:
        print(f"   ⚠️  Endpoint doesn't match expected format")
        print(f"   Expected format: https://<search-service-name>.search.windows.net")
    else:
        print(f"   ✅ Endpoint format looks correct")
    
    # Fix common issues
    print(f"\n3. Configuration Fixes:")
    fixed_endpoint = search_endpoint
    
    if search_endpoint and not search_endpoint.startswith('https://'):
        # Check if it's just the service name
        if not search_endpoint.startswith('http') and '.' not in search_endpoint:
            fixed_endpoint = f"https://{search_endpoint}.search.windows.net"
            print(f"   📝 Fixed endpoint (from service name): {fixed_endpoint}")
        else:
            fixed_endpoint = f"https://{search_endpoint}"
            print(f"   📝 Fixed endpoint (added https): {fixed_endpoint}")
    
    # Test connection
    print(f"\n4. Connection Test:")
    if fixed_endpoint and search_key:
        try:
            # Create index client
            index_client = SearchIndexClient(
                endpoint=fixed_endpoint,
                credential=AzureKeyCredential(search_key)
            )
            
            # Try to list indexes
            indexes = list(index_client.list_indexes())
            print(f"   ✅ Successfully connected to Azure Search")
            print(f"   Found {len(indexes)} indexes:")
            for idx in indexes:
                print(f"      - {idx.name}")
                
        except Exception as e:
            print(f"   ❌ Connection failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
    
    # Provide fix instructions
    print(f"\n5. Fix Instructions:")
    print("   Set your environment variables correctly:")
    print(f"   export AZURE_SEARCH_SERVICE_ENDPOINT='{fixed_endpoint}'")
    print(f"   export AZURE_SEARCH_ADMIN_KEY='<your-admin-key>'")
    print("\n   Or in your .env file:")
    print(f"   AZURE_SEARCH_SERVICE_ENDPOINT={fixed_endpoint}")
    print(f"   AZURE_SEARCH_ADMIN_KEY=<your-admin-key>")
    
    return fixed_endpoint, search_key

def test_simplechat_indexes(endpoint, key):
    """Test specific SimpleChat indexes"""
    print("\n=== Testing SimpleChat Indexes ===\n")
    
    if not endpoint or not key:
        print("❌ Cannot test - endpoint or key not provided")
        return
    
    try:
        index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        # Check for expected indexes
        expected_indexes = ['simplechat-user-index', 'simplechat-group-index']
        
        for index_name in expected_indexes:
            try:
                index = index_client.get_index(index_name)
                print(f"✅ Index '{index_name}' exists")
                print(f"   Fields: {len(index.fields)}")
            except Exception as e:
                print(f"❌ Index '{index_name}' not found: {str(e)}")
                
    except Exception as e:
        print(f"❌ Failed to check indexes: {str(e)}")

if __name__ == "__main__":
    fixed_endpoint, search_key = check_search_config()
    
    if fixed_endpoint and search_key:
        test_simplechat_indexes(fixed_endpoint, search_key)