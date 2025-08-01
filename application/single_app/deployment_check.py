import os
import sys
import dotenv
dotenv.load_dotenv()

def check_deployment_readiness():
    issues = []
    
    # Check for required files
    required_files = ['app.py', 'requirements.txt', 'config.py']
    for file in required_files:
        if not os.path.exists(file):
            issues.append(f"Missing required file: {file}")
    
    # Check for environment variables
    required_vars = ['AZURE_COSMOS_ENDPOINT', 'AZURE_COSMOS_KEY', 'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT']
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing environment variable: {var}")
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python version {sys.version} may not be compatible")
    
    if issues:
        print("Deployment issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Ready for deployment!")

if __name__ == "__main__":
    check_deployment_readiness()