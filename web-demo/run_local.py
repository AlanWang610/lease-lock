#!/usr/bin/env python3
"""
Local development server runner
Run this script to start the Flask development server
"""

import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the Flask app
from api.index import app

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Lease-Lock Demo Server")
    print("=" * 60)
    print("Access the demo at: http://localhost:5000")
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)

