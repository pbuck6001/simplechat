#!/usr/bin/env python3
"""
Azure Storage Connectivity Test Script
This script tests the Azure Storage configuration for the SimpleChatApp
"""

import os
import sys
import traceback
from datetime import datetime, timedelta

# Add the application directory to Python path
app_path = os.path.join(
    os.path.dirname(__file__), "simplechat", "application", "single_app"
)
sys.path.insert(0, app_path)

try:
    # Import configuration and required modules
    from config import *
    from functions_settings import *
    from azure.storage.blob import (
        BlobServiceClient,
        generate_blob_sas,
        BlobSasPermissions,
    )

    print("✅ Successfully imported required modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Make sure you're running this from the SimpleChatUpdated directory")
    sys.exit(1)


def test_storage_configuration():
    """Test Azure Storage configuration and connectivity"""
    print("\n🔍 Testing Azure Storage Configuration...")
    print("=" * 50)

    try:
        # Get settings
        print("1. Fetching application settings...")
        settings = get_settings()
        print("✅ Successfully retrieved settings from Cosmos DB")

        # Check storage client
        print("\n2. Checking storage client...")
        blob_service_client = CLIENTS.get("storage_account_office_docs_client")
        # blob_service_client = BlobServiceClient.from_connection_string(
        #       # <-- Expects connection string!
        # )
        if blob_service_client:
            print(f"✅ Storage client found: {type(blob_service_client)}")
            print(f"   Account name: {blob_service_client.account_name}")
        else:
            print("❌ Storage client not found in CLIENTS dictionary")
            print(f"   Available clients: {list(CLIENTS.keys())}")
            return False

        # Check storage key
        print("\n3. Checking storage account key...")
        storage_account_key = settings.get("office_docs_key")
        storage_account_key = "insert key here"
        if storage_account_key:
            print(f"✅ Storage key found (length: {len(storage_account_key)})")
            print(f"   Key starts with: {storage_account_key[:10]}...")
        else:
            print("❌ Storage key not found in settings")
            print("   Available setting keys containing 'storage' or 'key':")
            for key in settings.keys():
                if "storage" in key.lower() or "key" in key.lower():
                    print(f"     - {key}")
            return False

        # Check container configuration
        print("\n4. Checking container configuration...")
        container_name = storage_account_user_documents_container_name
        print(f"✅ Container name: '{container_name}' (length: {len(container_name)})")

        # Test container existence and creation
        print("\n5. Testing container access...")
        try:
            container_client = blob_service_client.get_container_client(container_name)
            exists = container_client.exists()
            print(f"✅ Container exists: {exists}")

            if not exists:
                print("   Attempting to create container...")
                container_client.create_container()
                print("✅ Container created successfully")
        except Exception as container_error:
            print(f"❌ Container access failed: {container_error}")
            return False

        # Test SAS token generation
        print("\n6. Testing SAS token generation...")
        try:
            test_blob_name = "test/sample.pdf"
            sas_token = generate_blob_sas(
                account_name=blob_service_client.account_name,
                container_name=container_name,
                blob_name=test_blob_name,
                account_key=storage_account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=1),
            )
            print(f"✅ SAS token generated successfully")
            print(f"   Token length: {len(sas_token)}")
            print(f"   Token starts with: {sas_token[:30]}...")
        except Exception as sas_error:
            print(f"❌ SAS token generation failed: {sas_error}")
            return False

        # Test signed URL construction
        print("\n7. Testing signed URL construction...")
        try:
            endpoint_suffix = "blob.core.windows.net"
            if AZURE_ENVIRONMENT == "usgovernment":
                endpoint_suffix = "blob.core.usgovcloudapi.net"
            if AZURE_ENVIRONMENT == "custom":
                endpoint_suffix = CUSTOM_BLOB_STORAGE_URL_VALUE

            signed_url = (
                f"https://{blob_service_client.account_name}.{endpoint_suffix}"
                f"/{container_name}/{test_blob_name}?{sas_token}"
            )
            print(f"✅ Signed URL constructed successfully")
            print(f"   URL: {signed_url[:100]}...")
        except Exception as url_error:
            print(f"❌ URL construction failed: {url_error}")
            return False

        print("\n🎉 All Azure Storage tests passed!")
        return True

    except Exception as e:
        print(f"❌ Storage configuration test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_enhanced_citations_config():
    """Test if Enhanced Citations is properly enabled"""
    print("\n🔍 Testing Enhanced Citations Configuration...")
    print("=" * 50)

    try:
        settings = get_settings()
        enable_enhanced_citations = settings.get("enable_enhanced_citations", False)

        print(f"Enhanced Citations enabled: {enable_enhanced_citations}")

        if not enable_enhanced_citations:
            print("⚠️  Enhanced Citations is not enabled in settings")
            print("   You may need to enable it in the Admin Settings page")
            return False
        else:
            print("✅ Enhanced Citations is enabled")
            return True

    except Exception as e:
        print(f"❌ Enhanced Citations config test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Azure Storage Connectivity Test for SimpleChatApp")
    print("=" * 60)

    # Test storage configuration
    storage_ok = test_storage_configuration()

    # Test enhanced citations config
    citations_ok = test_enhanced_citations_config()

    # Summary
    print("\n📊 Test Summary:")
    print("=" * 30)
    print(f"Storage Configuration: {'✅ PASS' if storage_ok else '❌ FAIL'}")
    print(f"Enhanced Citations:    {'✅ PASS' if citations_ok else '❌ FAIL'}")

    if storage_ok and citations_ok:
        print("\n🎉 All tests passed! Azure Storage should be working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")

    return storage_ok and citations_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
