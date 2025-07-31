import os
from dotenv import load_dotenv

load_dotenv()

print("Azure AD Configuration:")
print(f"Client ID: {os.environ.get('CLIENT_ID', 'NOT SET')}")
print(f"Tenant ID: {os.environ.get('TENANT_ID', 'NOT SET')}")
print(f"Redirect URI: {os.environ.get('REDIRECT_URI', 'NOT SET')}")

# Check if the redirect URI matches what the app is using
expected = "http://127.0.0.1:5000/getAToken"
actual = os.environ.get('REDIRECT_URI', expected)
print(f"\nExpected: {expected}")
print(f"Actual: {actual}")
print(f"Match: {expected == actual}")