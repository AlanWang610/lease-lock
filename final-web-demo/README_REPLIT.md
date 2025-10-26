# Deploy to Replit

## Steps

1. **Create a new Repl**:
   - Go to [replit.com](https://replit.com)
   - Click "Create Repl"
   - Choose "Python" template
   - Name it "lease-lock-demo"

2. **Import the code**:
   - Copy all files from the `web-demo` folder to your Repl
   - Important files:
     - `api/index.py` (main Flask app)
     - `api/demo_runner.py` (backend logic)
     - `templates/index.html`
     - `templates/lock.html`
     - `static/style.css`
     - `static/script.js`
     - `static/LeaseLock.png`

3. **Install dependencies**:
   - Replit will automatically install packages from `requirements.txt` when you run the Repl

4. **Run the app**:
   - Click the "Run" button
   - The Flask app will start on port 5000
   - A webview will open automatically showing your app

## Environment Variables

Set these in Replit Secrets (Tools → Secrets):
- `HORIZON_URL=https://horizon-testnet.stellar.org`
- `SOROBAN_RPC=https://soroban-testnet.stellar.org`
- `NETWORK_PASSPHRASE=Test SDF Network ; September 2015`
- `LANDLORD_SECRET=your_secret`
- `TENANT_SECRET=your_secret`
- `TENANT_SECRET=your_secret`
- `ARBITRATOR_SECRET=your_secret`
- `LESSOR_SECRET=your_secret`
- `REGISTRY_ID=your_contract_id`
- `ROOT_ID=1`
- `LEAF_ID=4`
- `UNIT=unitNYC123A`
- `PERIOD=2025-10`

## File Structure

```
web-demo/
├── .replit              # Replit configuration
├── replit.nix           # Package dependencies
├── api/
│   ├── index.py        # Main Flask app
│   └── demo_runner.py  # Backend logic
├── templates/
│   ├── index.html      # Main dashboard
│   └── lock.html       # Lock page
├── static/
│   ├── style.css       # Styles
│   ├── script.js       # Frontend logic
│   └── LeaseLock.png   # Logo
├── requirements.txt
└── README_REPLIT.md    # This file
```

## Features

- Dashboard with tabs (Auctions, Payments, Utilities, Lease Tree)
- Smart lock page (`/lock`) with keypad
- Real blockchain payment integration
- Mock SEP-10 and SEP-12 KYC flows
- Lease tree visualization
- Utilitarian spreadsheet-style design

