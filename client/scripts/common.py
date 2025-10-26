import os, requests, time
from dataclasses import dataclass
from dotenv import load_dotenv
from stellar_sdk import Server, Keypair

load_dotenv()

HORIZON = os.environ["HORIZON_URL"]
PASSPHRASE = os.environ["NETWORK_PASSPHRASE"]

server = Server(HORIZON)

@dataclass
class Actor:
    kp: Keypair

def actor_from_env(name: str) -> Actor:
    sec = os.environ[name]
    return Actor(kp=Keypair.from_secret(sec))

def ensure_funded(pubkey: str):
    # idempotent for testnet friendbot
    r = requests.get("https://friendbot.stellar.org", params={"addr": pubkey}, timeout=15)
    if r.status_code not in (200, 202, 400):  # 400 means already funded
        r.raise_for_status()
    # wait ledger close
    time.sleep(2)

def balances(pubkey: str):
    acct = server.accounts().account_id(pubkey).call()
    out = {}
    for b in acct["balances"]:
        code = "XLM" if b["asset_type"] == "native" else f'{b["asset_code"]}:{b["asset_issuer"]}'
        out[code] = b["balance"]
    return out
