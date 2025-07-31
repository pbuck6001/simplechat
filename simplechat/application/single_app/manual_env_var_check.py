import os
import sys
from pathlib import Path
import dotenv

print("   Environment before loading:")
test_var = "AZURE_OPENAI_API_KEY"
current_value = os.environ.get(test_var)
print(f"   {test_var} = {current_value}")

# Load .env
result = dotenv.load_dotenv(verbose=True, override=True)
print(f"   load_dotenv() returned: {result}")

# Check after loading
print("\n   Environment after loading:")
new_value = os.environ.get(test_var)
print(f"   {test_var} = {new_value}")