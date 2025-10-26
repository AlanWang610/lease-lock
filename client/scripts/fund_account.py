#!/usr/bin/env python3
"""
Fund a Stellar account with 100,000 XLM by creating multiple accounts,
funding them from friendbot, and merging them into the target account.
"""
import sys
import os
from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset, Payment
from stellar_sdk.exceptions import NotFoundError, BadRequestError
import time
from dotenv import load_dotenv

# Load config from the client directory
import os as os_module
script_dir = os_module.path.dirname(os_module.path.abspath(__file__))
env_path = os_module.path.join(script_dir, "../config.env")
load_dotenv(env_path)

HORIZON_URL = os.environ["HORIZON_URL"]
NETWORK_PASSPHRASE = os.environ["NETWORK_PASSPHRASE"]
server = Server(HORIZON_URL)

def fund_from_friendbot(pubkey: str):
    """Fund an account from friendbot."""
    import requests
    print(f"Requesting funds from friendbot for {pubkey}")
    r = requests.get("https://friendbot.stellar.org", params={"addr": pubkey}, timeout=15)
    if r.status_code == 200:
        print(f"[OK] Account {pubkey[:8]}... funded successfully")
        time.sleep(2)  # Wait for ledger close
        return True
    elif r.status_code == 400:
        print(f"[OK] Account {pubkey[:8]}... already funded")
        return True
    else:
        print(f"[ERROR] Failed to fund account: {r.status_code}")
        r.raise_for_status()
        return False

def get_balance(pubkey: str):
    """Get the XLM balance of an account."""
    try:
        account = server.accounts().account_id(pubkey).call()
        for balance in account["balances"]:
            if balance["asset_type"] == "native":
                return float(balance["balance"])
        return 0.0
    except NotFoundError:
        return 0.0

def send_all_xlm(source_kp: Keypair, dest_pubkey: str, memo_text: str = ""):
    """Send all XLM from source account to destination."""
    try:
        source_account = server.load_account(source_kp.public_key)
        
        # Get the balance
        balance = get_balance(source_kp.public_key)
        
        if balance < 2.0:  # Need at least 2 XLM for fees and reserve
            print(f"Skipping {source_kp.public_key[:8]}... - insufficient balance")
            return False
        
        # Reserve 2 XLM for fees and minimum balance
        amount_to_send = balance - 2.0
        
        if amount_to_send <= 0:
            print(f"Skipping {source_kp.public_key[:8]}... - nothing to send")
            return False
        
        print(f"Sending {amount_to_send:.4f} XLM from {source_kp.public_key[:8]}...")
        
        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=NETWORK_PASSPHRASE,
                base_fee=100
            )
            .append_operation(
                Payment(destination=dest_pubkey, asset=Asset.native(), amount=str(amount_to_send))
            )
            .add_text_memo(memo_text)
            .set_timeout(300)
            .build()
        )
        
        transaction.sign(source_kp)
        response = server.submit_transaction(transaction)
        print(f"[OK] Sent {amount_to_send:.4f} XLM successfully")
        print(f"  Transaction hash: {response['hash']}")
        time.sleep(1)  # Wait for ledger close
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send XLM: {e}")
        return False

def main():
    target_pubkey = "GC773P7BXH2I2MPHHYTDCRM66EBLEUUBSKHXN47E65Q6BAZ2DZVA6UQY"
    
    print(f"Funding target account: {target_pubkey}")
    print(f"This will create 10 accounts and merge them into the target\n")
    
    # Generate 10 source accounts
    source_keypairs = []
    print("Creating 10 source accounts...")
    for i in range(10):
        kp = Keypair.random()
        source_keypairs.append(kp)
        print(f"{i+1}. {kp.public_key}")
    
    print(f"\nFunding source accounts from friendbot...")
    for kp in source_keypairs:
        fund_from_friendbot(kp.public_key)
        time.sleep(0.5)
    
    print(f"\nSending all XLM to target account...")
    successful_transfers = 0
    for i, kp in enumerate(source_keypairs):
        print(f"\n[{i+1}/10] Processing {kp.public_key[:8]}...")
        if send_all_xlm(kp, target_pubkey, f"Funding #{i+1}"):
            successful_transfers += 1
    
    print(f"\n[OK] Completed!")
    print(f"  Successfully merged {successful_transfers} accounts")
    print(f"  Target account balance: {get_balance(target_pubkey):.4f} XLM")
    print(f"\nTarget account: {target_pubkey}")
    
    # Save the private keys for reference (optional)
    print(f"\nSource accounts used (private keys stored in memory, not saved)")
    for i, kp in enumerate(source_keypairs):
        print(f"{i+1}. {kp.public_key} (secret: {kp.secret[:10]}...)")

if __name__ == "__main__":
    main()

