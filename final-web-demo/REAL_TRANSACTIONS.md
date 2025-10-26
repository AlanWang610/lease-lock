# Real Blockchain Transactions

## Overview

The Lease-Lock Dashboard now executes **real blockchain transactions** on Stellar testnet for the payment functionality.

## What's Real vs Mocked

### Real Transactions ✅
- **Payment & Activation**: Sends actual XLM from tenant to landlord, then activates the lease on-chain
- Uses real Stellar SDK to build and submit transactions
- Transaction hashes are from actual blockchain submissions
- Explorer links point to real testnet transactions

### Mocked Transactions 🎭
- **Utilities Reading**: Simulated (for demo purposes)
- **Cost Splitting**: Calculated locally
- **Delinquency**: Simulated state change

## How It Works

### Payment Flow

1. **Real XLM Transfer**
   - Uses `stellar_sdk` to create payment transaction
   - Signs with tenant's secret key
   - Submits to Stellar testnet
   - Returns actual transaction hash

2. **Lease Activation**
   - Calls Soroban RPC to activate lease
   - Uses `LeaseAPI.set_active()` function
   - Submits to Soroban testnet contract
   - Returns activation transaction hash

### Fallback Behavior

If the real transaction fails (e.g., network error, insufficient funds, config issues), the system:
- Catches the exception
- Logs the error
- Falls back to mocked data
- Displays a note: "Using simulated data (real blockchain connection failed)"

## Configuration Required

The real payment requires these environment variables from `client/config.env`:

```env
# Network
HORIZON_URL=https://horizon-testnet.stellar.org
SOROBAN_RPC=https://soroban-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015

# Accounts (for real signing)
TENANT_SECRET=SC...
LANDLORD_SECRET=SC...
LESSOR_SECRET=SC...

# Contracts
REGISTRY_ID=...
```

## Testing

### Local Testing
```bash
cd web-demo
python run_local.py
```

### Expected Behavior

**Successful Transaction:**
- Click "Pay Rent & Activate"
- Real payment is submitted (takes ~5-10 seconds)
- Transaction hash is displayed
- Explorer link works
- Lock unlocks automatically

**Failed Transaction:**
- Real attempt fails
- Falls back to mock
- Shows note about simulated data
- UI still works (unlocks with mock hash)

## Transaction Details

### Payment Transaction
- **From**: Tenant account (from config)
- **To**: Landlord account (from config)
- **Amount**: 3.5 XLM (native asset)
- **Memo**: "rent"
- **Fee**: ~100 stroops
- **Network**: Stellar testnet

### Activation Transaction
- **Contract**: LeaseRegistry (REGISTRY_ID from config)
- **Function**: set_active
- **Signer**: Lessor account
- **Parameter**: Leaf lease ID
- **Network**: Soroban testnet

## Security Notes

⚠️ **Important**:
- Uses real secret keys (from config)
- Sends real XLM on testnet
- Only works if accounts are funded
- Check config.env for valid credentials

## Production Considerations

For production deployment:
1. Use environment variables, not config files
2. Add rate limiting on payment endpoint
3. Add authentication/authorization
4. Implement transaction confirmation tracking
5. Add wallet connection (Freighter, etc.)
6. Use mainnet with real XLM (be careful!)

## Troubleshooting

### "Real payment failed, using mock"

Common causes:
- Network connectivity issues
- Account not funded (check with friendbot)
- Invalid secret keys in config
- Contract not deployed
- Wrong network endpoint

**Solution**: Check your `client/config.env` file and ensure all credentials are correct.

### Transaction takes too long

The payment process involves:
1. Friendbot funding (if needed) ~2s
2. Transaction submission ~3-5s
3. Confirmation wait ~2s
4. Lease activation ~3-5s

**Total**: ~10-15 seconds is normal.

## Next Steps

To make other features real:
1. Update `mock_post_reading()` to execute real oracle calls
2. Update `mock_split_utilities()` to query real chain data
3. Update `mock_mark_delinquent()` to submit real state changes

