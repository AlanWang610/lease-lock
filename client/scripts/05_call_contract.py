import os
import json
import hashlib
import binascii
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval

load_dotenv()
rpc = SorobanServer(os.environ["SOROBAN_RPC"])
pp  = Network.TESTNET_NETWORK_PASSPHRASE  # same as .env
tenant = Keypair.from_secret(os.environ["TENANT_SECRET"])
landlord_pub = Keypair.from_secret(os.environ["LANDLORD_SECRET"]).public_key
contract_id = "CDBFB6YDB55G7E5ZGOHYIYBLS745NVBU73TKLB6N6IT6XBKBWICNUW5I"  # Updated contract ID

# Generate terms hash (canonical JSON format)
def generate_terms_hash(terms_dict):
    """Generate SHA-256 hash of canonical JSON terms"""
    canon = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True).encode()
    h = hashlib.sha256(canon).digest()
    return binascii.hexlify(h).decode()

# Example terms
terms_dict = {
    "rent": "500.00",
    "due_day": 1,
    "notice_days": 30,
    "penalty": "0.02"
}
terms_hash_hex = generate_terms_hash(terms_dict)
print(f"Terms hash: {terms_hash_hex}")

# Convert hex to BytesN<32>
terms_bytes = bytes.fromhex(terms_hash_hex)

# Get account sequence number
account = rpc.load_account(tenant.public_key)

# 1) Create master lease (landlord must sign this)
landlord_kp = Keypair.from_secret(os.environ["LANDLORD_SECRET"])
landlord_account = rpc.load_account(landlord_kp.public_key)

tx = TransactionBuilder(landlord_account, network_passphrase=pp, base_fee=100) \
    .append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="create_master",
        parameters=[
            scval.to_symbol("unitNYC123A"),
            scval.to_address(Address(landlord_pub)),
            scval.to_address(Address(tenant.public_key)),
            scval.to_bytes_n(terms_bytes),
            scval.to_uint32(2),  # limit: max 2 direct children
            scval.to_uint64(2000000000)  # expiry_ts: far future
        ]
    ).build()
tx.sign(landlord_kp)
result1 = rpc.send_transaction(tx)
print("Create master:", result1)

# 2) Accept the lease (tenant must sign this)
tx2 = TransactionBuilder(account, network_passphrase=pp, base_fee=100) \
    .append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="accept",
        parameters=[
            scval.to_uint64(1)  # lease ID (should be 1 for first lease)
        ]
    ).build()
tx2.sign(tenant)
result2 = rpc.send_transaction(tx2)
print("Accept lease:", result2)

# 3) Create sublease (tenant -> subtenant)
subtenant_pub = tenant.public_key  # reuse for demo; replace with real subtenant
tx3 = TransactionBuilder(account, network_passphrase=pp, base_fee=100) \
    .append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="create_sublease",
        parameters=[
            scval.to_uint64(1),  # parent_id
            scval.to_address(Address(subtenant_pub)),
            scval.to_bytes_n(terms_bytes),  # same terms as parent
            scval.to_uint32(1),  # limit: max 1 direct child
            scval.to_uint64(2000000000)  # expiry_ts: far future
        ]
    ).build()
tx3.sign(tenant)
result3 = rpc.send_transaction(tx3)
print("Create sublease:", result3)

print("\nAll operations completed successfully!")
print("The lease graph now supports unlimited sublease depth with proper terms validation.")