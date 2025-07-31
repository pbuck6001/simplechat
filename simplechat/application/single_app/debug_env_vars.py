import os
import sys
from pathlib import Path

print("=" * 60)
print("DEBUGGING ENVIRONMENT VARIABLES")
print("=" * 60)

# 1. Check current working directory
print("\n1. Current Working Directory:")
print(f"   {os.getcwd()}")

# 2. Check if .env file exists
print("\n2. Checking for .env file:")
env_path = Path(".env")
if env_path.exists():
    print(f"   ✅ .env file found at: {env_path.absolute()}")
    print(f"   File size: {env_path.stat().st_size} bytes")
    
    # Check if it's actually a file
    if env_path.is_file():
        print("   ✅ It is a file (not a directory)")
    else:
        print("   ❌ It is NOT a file - might be a directory!")
else:
    print("   ❌ .env file NOT found in current directory")
    
    # Look for .env in parent directories
    print("\n   Looking for .env in parent directories:")
    current = Path.cwd()
    for _ in range(3):  # Check up to 3 levels up
        current = current.parent
        env_check = current / ".env"
        if env_check.exists():
            print(f"   Found .env at: {env_check}")

# 3. Read .env file content (without dotenv)
print("\n3. Raw .env file content:")
if env_path.exists() and env_path.is_file():
    try:
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"   File length: {len(content)} characters")
        print("   First 200 characters (with hidden chars shown):")
        print("   " + "-" * 40)
        
        # Show content with hidden characters visible
        preview = content[:200]
        preview = preview.replace('\n', '\\n\n   ')
        preview = preview.replace('\r', '\\r')
        preview = preview.replace('\t', '\\t')
        print(f"   {preview}")
        print("   " + "-" * 40)
        
        # Check for common issues
        lines = content.strip().split('\n')
        print(f"\n   Number of lines: {len(lines)}")
        print("   First 3 lines (parsed):")
        for i, line in enumerate(lines[:3]):
            if line.strip():
                print(f"   Line {i+1}: '{line.strip()}'")
        
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")

# 4. Test manual parsing
print("\n4. Manual parsing test:")
if env_path.exists() and env_path.is_file():
    manual_vars = {}
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    manual_vars[key] = value
                    print(f"   Found: {key} = {value[:20]}..." if len(value) > 20 else f"   Found: {key} = {value}")
        
        print(f"\n   Total variables found manually: {len(manual_vars)}")
    except Exception as e:
        print(f"   ❌ Error in manual parsing: {e}")

# 5. Check if python-dotenv is installed
print("\n5. Checking python-dotenv:")
try:
    import dotenv
    print(f"   ✅ python-dotenv is installed (version: {dotenv.__version__ if hasattr(dotenv, '__version__') else 'unknown'})")
    
    # Try loading with dotenv
    print("\n6. Testing dotenv.load_dotenv():")
    
    # First, show current env vars (before loading)
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
    
    # Check all Azure-related env vars
    print("\n   All Azure-related environment variables:")
    azure_vars_found = 0
    for key in os.environ:
        if 'AZURE' in key.upper():
            value = os.environ[key]
            masked = f"{value[:3]}...{value[-3:]}" if len(value) > 10 else "*" * len(value)
            print(f"   {key} = {masked}")
            azure_vars_found += 1
    
    if azure_vars_found == 0:
        print("   ❌ No Azure variables found in environment")
    
except ImportError:
    print("   ❌ python-dotenv is NOT installed")
    print("   Install with: pip install python-dotenv")

# 7. Alternative test with explicit path
print("\n7. Testing with explicit .env path:")
try:
    from dotenv import load_dotenv
    env_full_path = Path(".env").absolute()
    print(f"   Loading from: {env_full_path}")
    result = load_dotenv(dotenv_path=env_full_path, override=True)
    print(f"   Result: {result}")
    
    # Test a variable
    test_value = os.environ.get("AZURE_OPENAI_API_KEY")
    if test_value:
        print(f"   ✅ Successfully loaded! Found API key: {test_value[:5]}...")
    else:
        print("   ❌ Still couldn't load variables")
        
except Exception as e:
    print(f"   Error: {e}")

# 8. Common issues checklist
print("\n8. Common Issues Checklist:")
print("   [ ] Is .env in the same directory as your Python script?")
print("   [ ] Does .env have the correct format (KEY=value)?")
print("   [ ] No spaces around the = sign?")
print("   [ ] No quotes needed (unless value has spaces)?")
print("   [ ] File saved with UTF-8 encoding?")
print("   [ ] No BOM (Byte Order Mark) at file start?")
print("   [ ] python-dotenv installed in your virtual environment?")

# 9. Show example .env format
print("\n9. Correct .env format example:")
print("   " + "-" * 40)
print("   AZURE_OPENAI_API_KEY=sk-1234567890abcdef")
print("   AZURE_OPENAI_ENDPOINT=https://myresource.openai.azure.com/")
print("   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo")
print("   " + "-" * 40)

print("\n" + "=" * 60)
print("END OF DEBUG REPORT")
print("=" * 60)