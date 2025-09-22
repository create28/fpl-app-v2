#!/usr/bin/env python3
"""
Local Development Runner for FPL Data Server
============================================

This script runs the FPL application locally for development purposes.
It sets the environment to 'local' and starts the server on localhost:8000.
"""

import os
import sys

def main():
    """Run the FPL app locally."""
    
    # Set environment variables for local development
    os.environ['ENVIRONMENT'] = 'local'
    os.environ['PORT'] = '8000'
    os.environ['HOST'] = 'localhost'
    
    print("🚀 Starting FPL Data Server (Local Development)")
    print("=" * 50)
    print("Environment: Local Development")
    print("Port: 8000")
    print("URL: http://localhost:8000")
    print("=" * 50)
    print()
    
    # Import and run the main application
    try:
        from main import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

