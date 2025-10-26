#!/usr/bin/env python3
"""
Flask Web Demo Application for Lease-Lock System

This is a Vercel serverless function that serves the demo interface
and provides API endpoints for each demo step.
"""

import os
import sys
import time
from flask import Flask, render_template, jsonify, request

# Add api directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demo_runner import (
    execute_pay_rent,  # Real payment execution
    mock_post_reading,
    execute_split_utilities,  # Real utility split calculation
    execute_place_bid  # Real auction bid placement
)

# Get the base directory (web-demo)
base_dir = os.path.join(os.path.dirname(__file__), '..')

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))


@app.route('/')
def index():
    """Serve the main demo page"""
    return render_template('index.html')


@app.route('/api/pay-rent', methods=['POST'])
def pay_rent():
    """Execute payment and activation demo - REAL blockchain transaction"""
    try:
        # Execute real blockchain payment
        result = execute_pay_rent()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/post-reading', methods=['POST'])
def post_reading():
    """Execute utility reading posting demo"""
    try:
        # Simulate processing time
        time.sleep(1)
        
        result = mock_post_reading()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/split-utilities', methods=['POST'])
def split_utilities():
    """Execute utility cost splitting demo - REAL calculation"""
    try:
        result = execute_split_utilities()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/place-bid', methods=['POST'])
def place_bid():
    """Place a bid on an auction - REAL blockchain transaction"""
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        
        result = execute_place_bid(amount)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# For Vercel deployment
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, lambda status, headers: None)


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)

