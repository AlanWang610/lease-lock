import os
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval

load_dotenv()
rpc = SorobanServer(os.environ["SOROBAN_RPC"])
pp  = Network.TESTNET_NETWORK_PASSPHRASE  # same as .env
tenant = Keypair.from_secret(os.environ["TENANT_SECRET"])
landlord_pub = Keypair.from_secret(os.environ["LANDLORD_SECRET"]).public_key
contract_id = "CAIGHDBLEXCGAUC7JTXSBZIW57RT4AHQL5XNZ6DLN2XWOOWMKAAAAS5B"  # converted from CBRYYKZFYRQFAX2M54QOKFXP4M7AB4C7N3OPQ23OV5TTVTCQ

# Get account sequence number
account = rpc.load_account(tenant.public_key)

# 1) register master (landlord must sign this)
landlord_kp = Keypair.from_secret(os.environ["LANDLORD_SECRET"])
landlord_account = rpc.load_account(landlord_kp.public_key)

tx = TransactionBuilder(landlord_account, network_passphrase=pp, base_fee=100) \
    .append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="register_master",
        parameters=[
            scval.to_symbol("unitNYC123A"),
            scval.to_address(Address(landlord_pub)),
            scval.to_address(Address(tenant.public_key))
        ]
    ).build()
tx.sign(landlord_kp)
print("Register master:", rpc.send_transaction(tx))

# 2) grant sublease (tenant -> subtenant mock)
subtenant_pub = tenant.public_key  # reuse for demo; replace with real
tx2 = TransactionBuilder(account, network_passphrase=pp, base_fee=100) \
    .append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="grant_sublease",
        parameters=[
            scval.to_symbol("unitNYC123A"),
            scval.to_address(Address(tenant.public_key)),
            scval.to_address(Address(subtenant_pub))
        ]
    ).build()
tx2.sign(tenant)
print("Grant sublease:", rpc.send_transaction(tx2))

# 3) read lineage
line = rpc.simulate_transaction(
    TransactionBuilder(account, network_passphrase=pp, base_fee=100)
    .append_invoke_contract_function_op(
        contract_id=contract_id,
        function_name="lineage",
        parameters=[scval.to_symbol("unitNYC123A")]
    ).build()
)
print("lineage:", line)
