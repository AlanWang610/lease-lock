#!/usr/bin/env python3
"""
Test script for the Mock Anchor Service
Simulates a wallet interacting with SEP-10, SEP-12, and SEP-24 endpoints
"""

import requests
import json
import time
import sys
from urllib.parse import urljoin

BASE_URL = "http://localhost:8001"
TEST_ACCOUNT = "GDEMOTESTACCOUNT123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def test_sep1_toml():
    """Test SEP-1: Stellar TOML"""
    print("Testing SEP-1: Stellar TOML...")
    
    try:
        response = requests.get(f"{BASE_URL}/.well-known/stellar.toml")
        response.raise_for_status()
        
        print("SUCCESS: SEP-1 TOML loaded successfully")
        print(f"   Content preview: {response.text[:200]}...")
        return True
    except Exception as e:
        print(f"ERROR: SEP-1 TOML failed: {e}")
        return False

def test_sep10_auth():
    """Test SEP-10: Authentication"""
    print("\nTesting SEP-10: Authentication...")
    
    try:
        # Get challenge
        response = requests.get(f"{BASE_URL}/auth", params={"account": TEST_ACCOUNT})
        response.raise_for_status()
        challenge_data = response.json()
        
        print(f"SUCCESS: Challenge received: {challenge_data}")
        
        # Submit challenge (mock)
        auth_data = {
            "account": TEST_ACCOUNT,
            "signed": "MOCK_SIGNATURE"
        }
        
        response = requests.post(f"{BASE_URL}/auth", json=auth_data)
        response.raise_for_status()
        token_data = response.json()
        
        print(f"SUCCESS: JWT token received: {token_data['token'][:50]}...")
        return token_data["token"]
        
    except Exception as e:
        print(f"ERROR: SEP-10 Auth failed: {e}")
        return None

def test_sep12_kyc(token):
    """Test SEP-12: KYC"""
    print("\nTesting SEP-12: KYC...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get KYC status
        response = requests.get(f"{BASE_URL}/kyc/customer", 
                              params={"account": TEST_ACCOUNT},
                              headers=headers)
        response.raise_for_status()
        kyc_status = response.json()
        
        print(f"SUCCESS: KYC status: {kyc_status}")
        
        # Submit KYC data
        kyc_data = {
            "account": TEST_ACCOUNT,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        response = requests.put(f"{BASE_URL}/kyc/customer", 
                              json=kyc_data,
                              headers=headers)
        response.raise_for_status()
        kyc_result = response.json()
        
        print(f"SUCCESS: KYC submitted: {kyc_result}")
        return True
        
    except Exception as e:
        print(f"ERROR: SEP-12 KYC failed: {e}")
        return False

def test_sep24_deposit(token):
    """Test SEP-24: Deposit"""
    print("\nTesting SEP-24: Deposit...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get interactive deposit URL
        response = requests.get(f"{BASE_URL}/sep24/transactions/deposit/interactive",
                              params={"asset_code": "USDTEST", "account": TEST_ACCOUNT},
                              headers=headers)
        response.raise_for_status()
        deposit_data = response.json()
        
        print(f"SUCCESS: Deposit URL: {deposit_data['url']}")
        
        # Extract transaction ID from URL
        tx_id = deposit_data['url'].split('tx=')[1]
        
        # Check transaction status
        response = requests.get(f"{BASE_URL}/sep24/transaction", params={"id": tx_id})
        response.raise_for_status()
        tx_data = response.json()
        
        print(f"SUCCESS: Transaction created: {tx_data['transaction']['id']}")
        
        # Simulate user clicking confirm (advance transaction)
        response = requests.post(f"{BASE_URL}/sep24/admin/advance",
                               params={"id": tx_id, "status": "pending_user_transfer_start"})
        response.raise_for_status()
        
        print("SUCCESS: Transaction advanced to pending_user_transfer_start")
        
        # Poll for completion
        print("Waiting for on-chain settlement...")
        for i in range(10):  # Poll for up to 20 seconds
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/sep24/transaction", params={"id": tx_id})
            response.raise_for_status()
            tx_data = response.json()
            
            status = tx_data['transaction']['status']
            print(f"   Status: {status}")
            
            if status == "completed":
                stellar_tx = tx_data['transaction'].get('stellar_transaction_id', 'N/A')
                print(f"SUCCESS: Deposit completed! Stellar TX: {stellar_tx}")
                return True
            elif status == "error":
                print(f"ERROR: Transaction failed: {tx_data['transaction'].get('error', 'Unknown error')}")
                return False
        
        print("TIMEOUT: Timeout waiting for completion")
        return False
        
    except Exception as e:
        print(f"ERROR: SEP-24 Deposit failed: {e}")
        return False

def test_sep24_withdraw(token):
    """Test SEP-24: Withdraw"""
    print("\nTesting SEP-24: Withdraw...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get interactive withdraw URL
        response = requests.get(f"{BASE_URL}/sep24/transactions/withdraw/interactive",
                              params={"asset_code": "USDTEST", "account": TEST_ACCOUNT},
                              headers=headers)
        response.raise_for_status()
        withdraw_data = response.json()
        
        print(f"SUCCESS: Withdraw URL: {withdraw_data['url']}")
        
        # Extract transaction ID from URL
        tx_id = withdraw_data['url'].split('tx=')[1]
        
        # Simulate user clicking confirm
        response = requests.post(f"{BASE_URL}/sep24/admin/advance",
                               params={"id": tx_id, "status": "pending_user_transfer_start"})
        response.raise_for_status()
        
        print("SUCCESS: Withdraw transaction advanced")
        
        # Poll for completion
        for i in range(5):
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/sep24/transaction", params={"id": tx_id})
            response.raise_for_status()
            tx_data = response.json()
            
            status = tx_data['transaction']['status']
            if status == "completed":
                stellar_tx = tx_data['transaction'].get('stellar_transaction_id', 'N/A')
                print(f"SUCCESS: Withdraw completed! Stellar TX: {stellar_tx}")
                return True
        
        print("TIMEOUT: Withdraw timeout")
        return False
        
    except Exception as e:
        print(f"ERROR: SEP-24 Withdraw failed: {e}")
        return False

def test_sep24_transactions(token):
    """Test SEP-24: Get all transactions"""
    print("\nTesting SEP-24: Get transactions...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/sep24/transactions",
                              params={"account": TEST_ACCOUNT},
                              headers=headers)
        response.raise_for_status()
        transactions_data = response.json()
        
        print(f"SUCCESS: Found {len(transactions_data['transactions'])} transactions")
        for tx in transactions_data['transactions']:
            print(f"   - {tx['id']}: {tx['kind']} ({tx['status']})")
        
        return True
        
    except Exception as e:
        print(f"ERROR: SEP-24 Get transactions failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Mock Anchor Service Tests")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Test Account: {TEST_ACCOUNT}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print("Server is running")
    except Exception as e:
        print(f"ERROR: Server not running: {e}")
        print("   Please start the server with: python main.py")
        sys.exit(1)
    
    # Run tests
    tests_passed = 0
    total_tests = 6
    
    if test_sep1_toml():
        tests_passed += 1
    
    token = test_sep10_auth()
    if token:
        tests_passed += 1
        
        if test_sep12_kyc(token):
            tests_passed += 1
        
        if test_sep24_deposit(token):
            tests_passed += 1
        
        if test_sep24_withdraw(token):
            tests_passed += 1
        
        if test_sep24_transactions(token):
            tests_passed += 1
    
    # Summary
    print(f"\nTest Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: All tests passed! Mock anchor is working correctly.")
    else:
        print("WARNING: Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()