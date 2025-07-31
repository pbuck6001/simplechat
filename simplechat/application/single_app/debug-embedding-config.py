# debug_embedding_config.py
# Debug script to check embedding model configuration

import os
import sys
from openai import AzureOpenAI
import openai
import dotenv

# Load .env
result = dotenv.load_dotenv(verbose=True, override=True)
print(f"   load_dotenv() returned: {result}")

def check_openai_config():
    print("=== OpenAI/Azure OpenAI Configuration Check ===\n")
    
    # Check for Azure OpenAI configuration
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    azure_key = os.getenv('AZURE_OPENAI_API_KEY', '')
    azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', '')
    azure_deployment = "text-embedding-3-small"
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    
    # Alternative env var names
    if not azure_endpoint:
        azure_endpoint = os.getenv('OPENAI_API_BASE', '')
    if not azure_key:
        azure_key = os.getenv('OPENAI_API_KEY', '')
    if not azure_deployment:
        azure_deployment = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT', '')
    
    print(f"1. Azure OpenAI Configuration:")
    print(f"   - Endpoint: {azure_endpoint if azure_endpoint else 'NOT SET'}")
    print(f"   - Key: {'Set' if azure_key else 'NOT SET'}")
    print(f"   - Deployment Name: {azure_deployment if azure_deployment else 'NOT SET'}")
    print(f"   - API Version: {api_version}")
    
    # Check for standard OpenAI configuration
    openai_key = os.getenv('OPENAI_API_KEY', '')
    print(f"\n2. Standard OpenAI Configuration:")
    print(f"   - API Key: {'Set' if openai_key else 'NOT SET'}")
    
    # Determine which mode is being used
    print(f"\n3. Configuration Mode:")
    if azure_endpoint and azure_key:
        print("   ✅ Using Azure OpenAI")
        mode = 'azure'
    elif openai_key and not azure_endpoint:
        print("   ✅ Using Standard OpenAI")
        mode = 'openai'
    else:
        print("   ❌ No valid OpenAI configuration found")
        mode = None
    
    return mode, {
        'azure_endpoint': azure_endpoint,
        'azure_key': azure_key,
        'azure_deployment': azure_deployment,
        'api_version': api_version,
        'openai_key': openai_key
    }

def test_embedding_model(mode, config):
    print(f"\n4. Testing Embedding Model:")
    
    if mode == 'azure':
        if not config['azure_deployment']:
            print("   ❌ Azure deployment name not set for embeddings")
            print("   Set AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT or AZURE_OPENAI_DEPLOYMENT_NAME")
            return
        
        try:
            client = AzureOpenAI(
                azure_endpoint=config['azure_endpoint'],
                api_key=config['azure_key'],
                api_version=config['api_version']
            )
            
            # Test embedding
            response = client.embeddings.create(
                input="Test embedding",
                model=config['azure_deployment']  # This should be your deployment name
            )
            
            print(f"   ✅ Successfully created embedding")
            print(f"   Embedding dimensions: {len(response.data[0].embedding)}")
            
        except Exception as e:
            print(f"   ❌ Failed to create embedding: {str(e)}")
            if "DeploymentNotFound" in str(e):
                print(f"   Check that '{config['azure_deployment']}' is a valid deployment name")
    
    elif mode == 'openai':
        try:
            openai.api_key = config['openai_key']
            
            # Test embedding
            response = openai.embeddings.create(
                input="Test embedding",
                model="text-embedding-ada-002"  # Standard OpenAI model
            )
            
            print(f"   ✅ Successfully created embedding")
            print(f"   Embedding dimensions: {len(response.data[0].embedding)}")
            
        except Exception as e:
            print(f"   ❌ Failed to create embedding: {str(e)}")

def check_simplechat_embedding_config():
    """Check how SimpleChat might be configured for embeddings"""
    print(f"\n5. SimpleChat Embedding Configuration Check:")
    
    # Common embedding-related environment variables
    embedding_vars = [
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT',
        'OPENAI_EMBEDDING_MODEL',
        'EMBEDDING_MODEL_NAME',
        'AZURE_OPENAI_DEPLOYMENT_NAME'
    ]
    
    print("   Checking for embedding-specific variables:")
    found_any = False
    for var in embedding_vars:
        value = os.getenv(var, '')
        if value:
            print(f"   ✅ {var} = {value}")
            found_any = True
    
    if not found_any:
        print("   ❌ No embedding-specific environment variables found")
        print("\n   Common deployment names for embeddings:")
        print("   - text-embedding-ada-002")
        print("   - text-embedding-3-small")
        print("   - text-embedding-3-large")

def provide_fix_instructions(mode, config):
    print(f"\n6. Fix Instructions:")
    
    if mode == 'azure':
        print("   For Azure OpenAI, ensure you have:")
        print("   1. Created an embedding model deployment in Azure")
        print("   2. Set the deployment name in your environment:")
        print("      export AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT='your-embedding-deployment-name'")
        print("\n   Example .env configuration:")
        print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("   AZURE_OPENAI_KEY=your-api-key")
        print("   AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-ada-002")
        print("   AZURE_OPENAI_API_VERSION=2024-02-15-preview")
    
    elif mode == 'openai':
        print("   For standard OpenAI, ensure you have:")
        print("   OPENAI_API_KEY=sk-...")
        print("\n   The embedding model 'text-embedding-ada-002' will be used by default")
    
    else:
        print("   You need to configure either Azure OpenAI or standard OpenAI:")
        print("\n   For Azure OpenAI:")
        print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("   AZURE_OPENAI_KEY=your-api-key")
        print("   AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=your-embedding-deployment")
        print("\n   For standard OpenAI:")
        print("   OPENAI_API_KEY=sk-...")

if __name__ == "__main__":
    mode, config = check_openai_config()
    
    if mode:
        test_embedding_model(mode, config)
    
    check_simplechat_embedding_config()
    provide_fix_instructions(mode, config)
    
    print("\n7. Next Steps:")
    print("   1. Set the missing environment variables")
    print("   2. Restart the application")
    print("   3. Try uploading a document again")
    print("   4. Check if the 'embedding_model' error is resolved")