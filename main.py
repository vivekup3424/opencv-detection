#!/usr/bin/env python3
"""
Main entry point for the Motion Detection System
Imports and runs the main function from the src package
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main function
from src.main import main

if __name__ == "__main__":
    main()