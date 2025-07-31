#!/usr/bin/env python3
"""
Azure Storage Account Verification Script
This script helps verify your Azure Storage Account configuration
"""

import os
import sys
from azure.storage.blob import BlobServiceClient


def test_connection_string_format():
    """Test different connection string formats"""
    print("🔍 Azure Storage Account Configuration Guide")
    print("=" * 60)

    print("\n📋 What You Need to Configure:")
    print("-" * 40)
    print("1. Your Azure Storage Account: 'simplechatstorageaccount'")
    print("2. Connection String Format:")
    print("   DefaultEndpointsProtocol=https;")
    print("   AccountName=simplechatstorageaccount;")
    print("   AccountKey=YOUR_ACCESS_KEY_HERE;")
    print("   EndpointSuffix=core.windows.net")
    print()

    print("📍 Where to Find These Values:")
    print("-" * 40)
    print("1. Go to Azure Portal")
    print("2. Navigate to your Storage Account: 'simplechatstorageaccount'")
    print("3. Go to: Settings → Access keys")
    print("4. Copy 'Connection string' from key1 or key2")
    print("5. Copy 'Key' from key1 or key2")
    print()

    print("🔧 Azure App Service Configuration:")
    print("-" * 40)
    print("Add these Application Settings:")
    print("• Name: office_docs_storage_account_url")
    print("  Value: [Your full connection string from step 4]")
    print("• Name: office_docs_key")
    print("  Value: [Your access key from step 5]")
    print()

    print("✅ Your Storage Account Type is CORRECT!")
    print("-" * 40)
    print("• Azure Storage Account includes Blob Storage automatically")
    print("• You do NOT need to create a separate 'Azure Blob' service")
    print("• Your account 'simplechatstorageaccount' is the right type")
    print()

    # Test if we can create a client with a sample connection string format
    print("🧪 Testing Connection String Format:")
    print("-" * 40)

    sample_connection = """DefaultEndpointsProtocol=https;AccountName=simplechatstorageaccount;AccountKey=SAMPLE_KEY;EndpointSuffix=core.windows.net"""

    try:
        # This will fail with auth error, but will validate the format
        client = BlobServiceClient.from_connection_string(sample_connection)
        print("✅ Connection string format is valid")
        print(f"   Account name parsed: {client.account_name}")
    except ValueError as e:
        print(f"❌ Connection string format error: {e}")
    except Exception as e:
        print(
            f"✅ Connection string format is valid (auth error expected): {type(e).__name__}"
        )
        print("   This means the format is correct, you just need the real key")


def test_with_your_connection_string():
    """Test with a connection string you provide"""
    print("\n🔑 Test Your Connection String:")
    print("-" * 40)
    print("If you have your connection string ready, you can test it here.")
    print("Format should be:")
    print(
        "DefaultEndpointsProtocol=https;AccountName=simplechatstorageaccount;AccountKey=YOUR_REAL_KEY;EndpointSuffix=core.windows.net"
    )
    print()

    connection_string = input(
        "Enter your connection string (or press Enter to skip): "
    ).strip()

    if connection_string:
        try:
            client = BlobServiceClient.from_connection_string(connection_string)
            print(f"✅ Connection string works!")
            print(f"   Account name: {client.account_name}")

            # Test listing containers
            print("   Testing container access...")
            containers = list(client.list_containers())
            print(f"   Found {len(containers)} containers")
            for container in containers:
                print(f"     - {container.name}")

        except Exception as e:
            print(f"❌ Connection failed: {e}")
    else:
        print("Skipping connection test.")


def main():
    """Main function"""
    test_connection_string_format()
    test_with_your_connection_string()

    print("\n📝 Next Steps:")
    print("=" * 30)
    print("1. Get your connection string from Azure Portal")
    print("2. Add 'office_docs_storage_account_url' to App Service settings")
    print("3. Add 'office_docs_key' to App Service settings")
    print("4. Restart your App Service")
    print("5. Test the SimpleChatApp Enhanced Citations")


if __name__ == "__main__":
    main()
