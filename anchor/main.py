from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import jwt
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import asyncio
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Payment, Asset
import os

app = FastAPI(title="Mock Anchor Service", version="1.0.0")

# Mount static files
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")

# Templates for UI
templates = Jinja2Templates(directory="templates")

# In-memory storage for demo
transactions: Dict[str, Dict[str, Any]] = {}
kyc_status: Dict[str, str] = {}

# JWT secret (in production, use a secure secret)
JWT_SECRET = "mock-anchor-secret-key"

# Mock anchor issuer account (you'll need to fund this with test XLM)
ANCHOR_ISSUER_SECRET = os.getenv("ANCHOR_ISSUER_SECRET", "SDEMOANCHORISSUER123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ANCHOR_ISSUER_PUBLIC = "GDEMOANCHORISSUER123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Stellar testnet server
server = Server("https://horizon-testnet.stellar.org")

def create_jwt_token(account: str) -> str:
    """Create a JWT token for the given account"""
    payload = {
        "iss": "mock-anchor",
        "sub": account,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> Optional[str]:
    """Verify JWT token and return account"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def pay_xlm(src_secret: str, dest_account: str, amount: str) -> str:
    """Send XLM from anchor to user account"""
    try:
        src_keypair = Keypair.from_secret(src_secret)
        source_account = server.load_account(src_keypair.public_key)
        
        transaction = (TransactionBuilder(source_account, Network.TESTNET_NETWORK_PASSPHRASE, base_fee=100)
                      .append_operation(Payment(destination=dest_account, asset=Asset.native(), amount=amount))
                      .set_timeout(60)
                      .build())
        
        transaction.sign(src_keypair)
        response = server.submit_transaction(transaction)
        return response["hash"]
    except Exception as e:
        print(f"Error sending XLM: {e}")
        return f"mock-hash-{uuid.uuid4().hex[:8]}"

# SEP-10 Authentication endpoints
@app.get("/auth")
async def get_auth_challenge(account: str):
    """SEP-10: Get authentication challenge"""
    return {
        "transaction": "CHALLENGE_STUB",
        "network_passphrase": "Test SDF Network ; September 2015"
    }

@app.post("/auth")
async def submit_auth_challenge(request: Request):
    """SEP-10: Submit authentication challenge"""
    body = await request.json()
    account = body.get("account")
    
    if not account:
        raise HTTPException(status_code=400, detail="Account required")
    
    token = create_jwt_token(account)
    return {"token": token}

# SEP-12 KYC endpoints
@app.get("/kyc/customer")
async def get_kyc_status(account: str, token: str = Depends(verify_jwt_token)):
    """SEP-12: Get KYC status"""
    if account not in kyc_status:
        kyc_status[account] = "NEEDS_INFO"
    
    if kyc_status[account] == "NEEDS_INFO":
        return {
            "status": "NEEDS_INFO",
            "fields": ["first_name", "last_name", "email"]
        }
    else:
        return {"status": kyc_status[account]}

@app.put("/kyc/customer")
async def update_kyc_status(request: Request, token: str = Depends(verify_jwt_token)):
    """SEP-12: Update KYC status"""
    body = await request.json()
    account = body.get("account", token)  # Use token's account if not provided
    
    # Accept any KYC data and mark as accepted
    kyc_status[account] = "ACCEPTED"
    return {"status": "ACCEPTED"}

# SEP-24 Transaction endpoints
@app.get("/sep24/transactions/deposit/interactive")
async def get_deposit_interactive(
    asset_code: str = "USDTEST",
    account: str = None,
    token: str = Depends(verify_jwt_token)
):
    """SEP-24: Get interactive deposit URL"""
    if not account:
        account = token
    
    tx_id = str(uuid.uuid4())
    transactions[tx_id] = {
        "id": tx_id,
        "kind": "deposit",
        "status": "incomplete",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "amount_in": "0",
        "amount_out": "0",
        "amount_fee": "0",
        "account": account,
        "asset_code": asset_code
    }
    
    return {
        "url": f"http://localhost:8001/sep24/webapp/deposit?tx={tx_id}"
    }

@app.get("/sep24/transactions/withdraw/interactive")
async def get_withdraw_interactive(
    asset_code: str = "USDTEST",
    account: str = None,
    token: str = Depends(verify_jwt_token)
):
    """SEP-24: Get interactive withdraw URL"""
    if not account:
        account = token
    
    tx_id = str(uuid.uuid4())
    transactions[tx_id] = {
        "id": tx_id,
        "kind": "withdraw",
        "status": "incomplete",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "amount_in": "0",
        "amount_out": "0",
        "amount_fee": "0",
        "account": account,
        "asset_code": asset_code
    }
    
    return {
        "url": f"http://localhost:8001/sep24/webapp/withdraw?tx={tx_id}"
    }

@app.get("/sep24/transaction")
async def get_transaction(id: str):
    """SEP-24: Get transaction status"""
    if id not in transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"transaction": transactions[id]}

@app.get("/sep24/transactions")
async def get_transactions(account: str, token: str = Depends(verify_jwt_token)):
    """SEP-24: Get all transactions for account"""
    account_transactions = [tx for tx in transactions.values() if tx["account"] == account]
    return {"transactions": account_transactions}

# Mock interactive UI pages
@app.get("/sep24/webapp/deposit", response_class=HTMLResponse)
async def deposit_webapp(request: Request, tx: str):
    """Mock deposit webapp"""
    if tx not in transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return templates.TemplateResponse("deposit.html", {
        "request": request,
        "tx_id": tx,
        "transaction": transactions[tx]
    })

@app.get("/sep24/webapp/withdraw", response_class=HTMLResponse)
async def withdraw_webapp(request: Request, tx: str):
    """Mock withdraw webapp"""
    if tx not in transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return templates.TemplateResponse("withdraw.html", {
        "request": request,
        "tx_id": tx,
        "transaction": transactions[tx]
    })

@app.post("/sep24/admin/advance")
async def advance_transaction(id: str, status: str):
    """Internal endpoint to advance transaction status"""
    if id not in transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    tx = transactions[id]
    tx["status"] = status
    
    # If moving to pending_user_transfer_start, trigger on-chain settlement
    if status == "pending_user_transfer_start":
        tx["amount_in"] = "5.0"
        tx["amount_out"] = "5.0"
        
        # Trigger async settlement
        asyncio.create_task(settle_transaction(id))
    
    elif status == "completed":
        tx["completed_at"] = datetime.utcnow().isoformat() + "Z"
    
    return {"status": "success"}

async def settle_transaction(tx_id: str):
    """Settle transaction on-chain"""
    tx = transactions[tx_id]
    
    try:
        if tx["kind"] == "deposit":
            # Send XLM to user (deposit)
            hash_result = await pay_xlm(ANCHOR_ISSUER_SECRET, tx["account"], "5.0")
            tx["stellar_transaction_id"] = hash_result
            tx["status"] = "completed"
            tx["completed_at"] = datetime.utcnow().isoformat() + "Z"
            
        elif tx["kind"] == "withdraw":
            # For withdraw, we'd normally pull from user, but for demo we'll just mark complete
            tx["stellar_transaction_id"] = f"mock-withdraw-{uuid.uuid4().hex[:8]}"
            tx["status"] = "completed"
            tx["completed_at"] = datetime.utcnow().isoformat() + "Z"
            
    except Exception as e:
        print(f"Error settling transaction {tx_id}: {e}")
        tx["status"] = "error"
        tx["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
