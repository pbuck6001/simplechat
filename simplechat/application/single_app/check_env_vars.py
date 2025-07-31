import os
import sys
from datetime import datetime
import dotenv

# Load .env
result = dotenv.load_dotenv(verbose=True, override=True)
print(f"   load_dotenv() returned: {result}")

def check_env_variable(var_name, required=True):
    """Check if an environment variable exists and has a value."""
    value = os.environ.get(var_name)
    
    if value:
        # Mask the value for security (show only first and last 3 chars if long enough)
        if len(value) > 10:
            masked_value = f"{value[:3]}{'*' * (len(value) - 6)}{value[-3:]}"
        else:
            masked_value = '*' * len(value)
        
        print(f"✅ {var_name}: Found (value: {masked_value})")
        return True
    else:
        if required:
            print(f"❌ {var_name}: NOT FOUND - This is required!")
        else:
            print(f"⚠️  {var_name}: Not found (optional)")
        return False

def main():
    print("=" * 60)
    print("Azure Environment Variables Checker")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    
        
    # Common Azure environment variables for Simple Chat
    # Adjust these based on your specific Azure services
    required_vars = [
        # Azure OpenAI / Cognitive Services
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        
        # Azure Storage (if using blob storage)
        # "AZURE_STORAGE_CONNECTION_STRING",
        
        # Azure Cosmos DB (if using)
        "AZURE_COSMOS_ENDPOINT",
        "AZURE_COSMOS_KEY",
        
        # Azure App Configuration (if using)
        # "AZURE_APP_CONFIG_CONNECTION_STRING",
        
        # Azure Key Vault (if using)
        # "AZURE_KEY_VAULT_URL",
        
        # Azure Active Directory (if using)
        "CLIENT_ID",
        "SECRET_KEY",
        "TENANT_ID",
    ]
    
    optional_vars = [
        # Additional optional configurations
        "AZURE_OPENAI_API_VERSION",
        "AZURE_REGION",
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP",
    ]
    
    print("Checking Required Environment Variables:")
    print("-" * 40)
    required_found = 0
    for var in required_vars:
        if check_env_variable(var, required=True):
            required_found += 1
    
    print(f"\nRequired variables found: {required_found}/{len(required_vars)}")
    
    print("\n\nChecking Optional Environment Variables:")
    print("-" * 40)
    optional_found = 0
    for var in optional_vars:
        if check_env_variable(var, required=False):
            optional_found += 1
    
    print(f"\nOptional variables found: {optional_found}/{len(optional_vars)}")
    
    # Check for .env file
    print("\n\nChecking for .env file:")
    print("-" * 40)
    if os.path.exists('.env'):
        print("✅ .env file found in current directory")
        
        # Check if python-dotenv is installed
        try:
            import dotenv
            print("✅ python-dotenv is installed")
            print("   Tip: Use 'dotenv.load_dotenv()' in your code to load .env file")
        except ImportError:
            print("⚠️  python-dotenv is NOT installed")
            print("   Install with: pip install python-dotenv")
    else:
        print("❌ No .env file found in current directory")
        print("   Consider creating one for local development")
    
    # Summary and recommendations
    print("\n\n" + "=" * 60)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    
    if required_found == 0:
        print("\n⚠️  WARNING: No required environment variables found!")
        print("\nTo set environment variables:")
        print("  - Windows (Command Prompt): set VARIABLE_NAME=value")
        print("  - Windows (PowerShell): $env:VARIABLE_NAME='value'")
        print("  - Linux/Mac: export VARIABLE_NAME=value")
        print("\nOr create a .env file with:")
        print("  AZURE_OPENAI_API_KEY=your-key-here")
        print("  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("  etc...")
    elif required_found < len(required_vars):
        print(f"\n⚠️  Some required variables are missing ({len(required_vars) - required_found} missing)")
        print("Please set the missing environment variables before proceeding.")
    else:
        print("\n✅ All required environment variables are set!")
        print("You're ready to proceed with testing Azure services.")
    
    # Test loading from .env file if it exists
    if os.path.exists('.env'):
        try:
            from dotenv import load_dotenv
            print("\n\nTesting .env file loading...")
            print("-" * 40)
            load_dotenv(override=True)
            print("✅ Successfully loaded .env file")
            print("   Re-checking variables after loading .env...")
            
            # Quick re-check of a key variable
            if os.environ.get("AZURE_OPENAI_API_KEY"):
                print("   ✅ Variables loaded from .env file successfully")
        except ImportError:
            pass

if __name__ == "__main__":
    main()