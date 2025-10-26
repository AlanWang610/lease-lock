#!/bin/bash
# Lock Daemon Runner Script

# Check if .env file exists
if [ -f ".env" ]; then
    echo "Loading environment from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if LEASE_REGISTRY_ID is set
if [ -z "$LEASE_REGISTRY_ID" ]; then
    echo "Error: LEASE_REGISTRY_ID environment variable is required"
    echo "Set it in your environment or create a .env file with:"
    echo "LEASE_REGISTRY_ID=your_contract_id_here"
    exit 1
fi

echo "Starting Lock Daemon..."
echo "Contract ID: $LEASE_REGISTRY_ID"
echo "RPC Endpoint: ${STELLAR_RPC:-https://soroban-testnet.stellar.org}"
echo ""

# Run the daemon
python iot_lock_daemon.py
