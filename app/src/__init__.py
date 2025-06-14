# src/__init__.py
"""
Main package initialization for the multi-agent AI application.
"""
# Remove the circular import - don't import from src
# Instead, import directly from the specific modules
# If you need to expose certain functions at the package level,
# import them directly from their modules:
# Example of correct imports (adjust based on your actual module structure):
# from .auth import login_required, check_authentication
# from .config import get_settings
# from .utils import some_utility_function

# For now, let's keep it minimal to avoid circular imports
__version__ = "1.0.0"
__author__ = "Abiola Shittu"

# Only define what's absolutely necessary here
# Most imports should be done directly in the files that need them