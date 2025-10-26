import os
from stellar_sdk import Server, Keypair, TransactionBuilder, Network
from dotenv import load_dotenv
load_dotenv()
server = Server(os.environ["HORIZON_URL"])
pp = os.environ["NETWORK_PASSPHRASE"]

# choose who claims:
claimer = Keypair.from_secret(os.environ["ARBITRATOR_SECRET"])
BALANCE_ID = os.environ["BALANCE_ID"]  # set from the curl output

src = server.load_account(claimer.public_key)
tx = (TransactionBuilder(src, network_passphrase=pp, base_fee=100)
      .append_claim_claimable_balance_op(BALANCE_ID)
      .set_timeout(60)
      .build())
tx.sign(claimer)
print(server.submit_transaction(tx)["hash"])
