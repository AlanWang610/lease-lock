import os
from stellar_sdk import (
    Server, Keypair, TransactionBuilder, Network, Payment, Asset
)
from dotenv import load_dotenv
load_dotenv()

server = Server(os.environ["HORIZON_URL"])
pp = os.environ["NETWORK_PASSPHRASE"]

tenant = Keypair.from_secret(os.environ["TENANT_SECRET"])
landlord_pub = Keypair.from_secret(os.environ["LANDLORD_SECRET"]).public_key

src = server.load_account(tenant.public_key)
tx = (TransactionBuilder(src, network_passphrase=pp, base_fee=100)
      .add_text_memo("rent-2025-10")
      .append_operation(Payment(destination=landlord_pub, asset=Asset.native(), amount="5"))
      .set_timeout(60)
      .build())
tx.sign(tenant)
resp = server.submit_transaction(tx)
print("hash:", resp["hash"])
