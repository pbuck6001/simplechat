from openai import AzureOpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file (optional)
load_dotenv()

# Azure OpenAI configuration
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://simple-chat-azure-openai.openai.azure.com/")
API_KEY = os.getenv("AZURE_OPENAI_KEY", "insert-key-here")  # Replace with your actual key
MODEL_NAME = "gpt-4o"  # Your deployed model name
API_VERSION = "2024-12-01-preview"  # Stable API version compatible with gpt-4o

def test_openai_deployment():
    try:
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            azure_endpoint=ENDPOINT,
            api_key=API_KEY,
            api_version=API_VERSION
        )

        print(f"Testing connection to Azure OpenAI endpoint: {ENDPOINT}")
        print(f"Using model: {MODEL_NAME}")

        # Test chat completion
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, world! Can you respond?"}
            ],
            max_tokens=50
        )

        # Print response
        print("\nSuccess! Model response:")
        print(response.choices[0].message.content)

    except Exception as e:
        print(f"\nError: Failed to connect or get response from model")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    # Verify configuration
    if not ENDPOINT or not API_KEY:
        print("Error: AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_KEY not set")
    else:
        test_openai_deployment()
