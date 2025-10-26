# Testing the Real Payment Integration

## What Was Fixed

The issue was with the path resolution in `demo_runner.py`. We needed to properly navigate from the web-demo directory structure to the client scripts.

### Original Problem
```python
# This was going: web-demo/api -> up -> web-demo -> client/scripts (WRONG)
client_scripts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client', 'scripts')
```

### Fix
```python
# This goes: web-demo/api/demo_runner.py -> up to root (lease-lock) -> client/scripts
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
client_scripts_path = os.path.join(project_root, 'client', 'scripts')
```

## How to Test

1. **Start the Flask app:**
   ```bash
   cd web-demo
   python run_local.py
   ```

2. **Open the browser:**
   ```
   http://localhost:5000
   ```

3. **Click "Pay Rent & Activate"**
   - Should attempt real blockchain transaction
   - May take 10-15 seconds
   - Will fall back to mock if it fails

## Expected Behavior

### Success Case
- Real Stellar transaction is submitted
- Transaction hash from blockchain
- Actual account addresses shown
- Explorer link works
- Lock unlocks

### Failure Case
- Attempts real transaction
- Catches error
- Falls back to mock
- Shows note: "Using simulated data (real blockchain connection failed)"
- UI still works with mock data

## Troubleshooting

If you see "No module named 'common'":
- Check that you're running from `web-demo` directory
- Verify `client/scripts/common.py` exists
- Verify path resolution logic

If you see network errors:
- Check your internet connection
- Verify Stellar testnet is accessible
- Check `HORIZON_URL` in config.env

If you see "account not found":
- Ensure accounts are funded on testnet
- Friendbot should fund them automatically
- May take a few seconds on first run

