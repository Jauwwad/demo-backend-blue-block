#!/usr/bin/env python3
"""
Startup script for Blue Carbon MRV System on Render
"""
import os
import sys

if __name__ == "__main__":
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import and run the main production server
    from production_serverMAIN import main
    main()