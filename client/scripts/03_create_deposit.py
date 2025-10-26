import os, time
from stellar_sdk import (
    Server, Keypair, TransactionBuilder, Network, Asset,
    Claimant, ClaimPredicate
)
from dotenv import load_dotenv
load_dotenv()

server = Server(os.environ["HORIZON_URL"])
pp = os.environ["NETWORK_PASSPHRASE"]

tenant = Keypair.from_secret(os.environ["TENANT_SECRET"])
landlord_pub = Keypair.from_secret(os.environ["LANDLORD_SECRET"]).public_key
arbitrator_pub = Keypair.from_secret(os.environ["ARBITRATOR_SECRET"]).public_key

# Timelock: claimable by landlord after now+3 minutes. Arbitrator can claim anytime.
now_unix = int(server.root().call()["history_latest_ledger"])  # cheap stand-in; better: time.time()
abs_time = int(time.time()) + 180

predicate_after = ClaimPredicate.predicate_not(
    ClaimPredicate.predicate_before_absolute_time(abs_time)
)
predicate_anytime = ClaimPredicate.predicate_unconditional()

claimant_landlord  = Claimant(landlord_pub, predicate_after)
claimant_arbit     = Claimant(arbitrator_pub, predicate_anytime)

src = server.load_account(tenant.public_key)
tx = (TransactionBuilder(src, network_passphrase=pp, base_fee=100)
      .append_create_claimable_balance_op(
          asset=Asset.native(), amount="10",
          claimants=[claimant_landlord, claimant_arbit]
      )
      .set_timeout(60)
      .build())
tx.sign(tenant)
resp = server.submit_transaction(tx)
print("created:", resp["hash"])
