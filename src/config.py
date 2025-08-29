"""
Central configuration module for loading environment variables.
Import this module at the top of any file that needs environment variables.
"""

import os
import pathlib
from dotenv import load_dotenv

# Get the project root directory (parent of src)
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.absolute()

# Load environment variables from .env file in project root
dotenv_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Create convenience functions to access common environment variables
def get_api_key(key_name):
    """Get an API key from environment variables."""
    api_key = os.getenv(key_name)
    if not api_key:
        print(f"Warning: {key_name} not found in environment variables")
    return api_key

# Example usage:
# BRAVE_SEARCH_API_KEY = get_api_key("BRAVE_SEARCH_API_KEY")
