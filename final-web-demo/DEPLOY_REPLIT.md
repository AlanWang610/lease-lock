# Deploy to Replit - Quick Start

## 1. Create Repl

1. Go to [replit.com](https://replit.com) and sign in
2. Click "+ Create Repl"
3. Search for "Python" and select it
4. Name it "lease-lock-demo"
5. Click "Create Repl"

## 2. Upload Files

Upload the entire `web-demo` folder contents to your Repl. Key files needed:

```
web-demo/
├── api/
│   ├── index.py
│   └── demo_runner.py
├── templates/
│   ├── index.html
│   └── lock.html
├── static/
│   ├── style.css
│   ├── script.js
│   └── LeaseLock.png
├── requirements.txt
├── .replit
└── replit.nix
```

## 3. Set Environment Variables

Click the "Secrets" (🔒) icon in the sidebar and add:

```
HORIZON_URL=https://horizon-testnet.stellar.org
SOROBAN_RPC=https://soroban-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015
LANDLORD_SECRET=your_secret_here
TENANT_SECRET=your_secret_here
ARBITRATOR_SECRET=your_secret_here
LESSOR_SECRET=your_secret_here
REGISTRY_ID=your_contract_id
ROOT_ID=1
LEAF_ID=4
UNIT=unitNYC123A
PERIOD=2025-10
```

## 4. Run

1. Click the "Run" button (▶️) at the top
2. Replit will install dependencies from `requirements.txt`
3. The Flask app starts on port 5000
4. A webview opens automatically with your dashboard

## 5. Access the App

- **Main dashboard**: Shown in the webview
- **Lock page**: Use the URL shown + `/lock`

## Troubleshooting

### If packages don't install:
Run in the shell:
```bash
pip install -r requirements.txt
```

### If the app doesn't start:
Check the Run button output for errors. Make sure:
- All files are uploaded correctly
- Environment variables are set
- `requirements.txt` is in the root

### Port already in use:
Replit will automatically assign a port. Check the output panel for the URL.

## Features Available

- ✅ Auction bidding (second-price)
- ✅ Payment with SEP-10/SEP-12
- ✅ Utilities cost splitting
- ✅ Lease tree visualization
- ✅ Smart lock with keypad (/lock)
- ✅ Utilitarian spreadsheet design

