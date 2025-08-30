# This file makes src a package
import os
import pathlib
from dotenv import load_dotenv

# Get the project root directory
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.absolute()

# Load environment variables from .env file in project root
dotenv_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Main exports
from .orchestrator import Orchestrator

__all__ = ['Orchestrator']
