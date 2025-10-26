# Mock Anchor Service

A complete mock implementation of Stellar Anchor endpoints (SEP-1, SEP-10, SEP-12, SEP-24) that settles transactions on-chain with testnet XLM.

## Features

- **SEP-1**: Serves `stellar.toml` configuration
- **SEP-10**: Web authentication with JWT tokens
- **SEP-12**: KYC status management
- **SEP-24**: Interactive deposit/withdraw flows
- **On-chain Settlement**: Real testnet XLM transactions
- **Mock UI**: Web interface for transaction confirmation

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   python main.py
   ```

3. **Run tests**:
   ```bash
   python test_anchor.py
   ```

The server will be available at `http://localhost:8000`

## API Endpoints

### SEP-1: Stellar TOML
- `GET /.well-known/stellar.toml` - Anchor configuration

### SEP-10: Authentication
- `GET /auth?account=G...` - Get authentication challenge
- `POST /auth` - Submit challenge and get JWT token

### SEP-12: KYC
- `GET /kyc/customer?account=G...` - Get KYC status
- `PUT /kyc/customer` - Submit KYC information

### SEP-24: Transactions
- `GET /sep24/transactions/deposit/interactive` - Start deposit flow
- `GET /sep24/transactions/withdraw/interactive` - Start withdraw flow
- `GET /sep24/transaction?id=...` - Get transaction status
- `GET /sep24/transactions?account=G...` - List account transactions

### Mock UI
- `GET /sep24/webapp/deposit?tx=...` - Deposit confirmation page
- `GET /sep24/webapp/withdraw?tx=...` - Withdraw confirmation page

## Configuration

### Environment Variables

- `ANCHOR_ISSUER_SECRET`: Secret key for the anchor issuer account (defaults to demo key)

### Funding the Anchor Account

To enable real on-chain settlements, you need to fund the anchor issuer account with testnet XLM:

1. Get the public key: `GDEMOANCHORISSUER123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`
2. Fund it using the [Stellar Testnet Faucet](https://laboratory.stellar.org/#account-creator?network=testnet)
3. Or set `ANCHOR_ISSUER_SECRET` to your own funded account's secret key

## Testing

The `test_anchor.py` script simulates a complete wallet flow:

1. Fetches the stellar.toml configuration
2. Authenticates using SEP-10
3. Completes KYC using SEP-12
4. Initiates a deposit using SEP-24
5. Confirms the transaction via the mock UI
6. Polls for completion and displays the on-chain transaction hash

## Transaction Flow

1. **Deposit Flow**:
   - User requests deposit URL
   - User visits confirmation page
   - User clicks "Confirm Deposit"
   - Anchor sends 5 XLM to user's account
   - Transaction marked as completed

2. **Withdraw Flow**:
   - User requests withdraw URL
   - User visits confirmation page
   - User clicks "Confirm Withdraw"
   - Transaction marked as completed (mock settlement)

## Development Notes

- All data is stored in memory (resets on restart)
- JWT tokens expire after 1 hour
- Transactions settle with 5 XLM for demo purposes
- Error handling includes fallback to mock transaction hashes
- The service uses Stellar testnet for real blockchain interactions

## Production Considerations

For production use, consider:

- Persistent database storage
- Proper secret key management
- Rate limiting and security measures
- Real KYC integration
- Proper error handling and logging
- HTTPS endpoints
- Database migrations
- Monitoring and alerting
