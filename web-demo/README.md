# Lease-Lock System Web Demo

A Flask web application that demonstrates the end-to-end lease-lock workflow including payments, lock activation, utility management, and delinquency handling.

## Overview

This demo showcases the complete lease-lock system built on Stellar blockchain with Soroban smart contracts. The web interface provides an interactive demonstration of:

1. **Payment & Activation**: Pay rent and activate lease (unlocks door)
2. **Utility Reading**: Post utility meter readings to blockchain
3. **Cost Splitting**: Split utility costs among active leases
4. **Delinquency**: Mark lease as delinquent (locks door)

## Architecture

This is a mock demonstration that simulates the execution of the actual Python demo scripts without executing real blockchain transactions. It uses the configuration from `../client/config.env` to display realistic transaction hashes and account addresses.

### Key Features

- Clean, modern web interface
- Step-by-step demonstration flow
- Realistic transaction hash generation
- Stellar testnet explorer links
- Progress tracking
- Sequential execution mode

## Local Development

### Prerequisites

- Python 3.8+
- Flask

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure `../client/config.env` exists with valid configuration

3. Run the Flask app:
```bash
python api/index.py
```

4. Open http://localhost:5000 in your browser

## Deployment to Vercel

### Method 1: Vercel CLI

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
cd web-demo
vercel
```

4. Follow the prompts to configure your project

### Method 2: GitHub Integration

1. Push your code to GitHub

2. Go to https://vercel.com/new

3. Import your repository

4. Vercel will auto-detect the Flask app and deploy

5. Configure environment variables in Vercel dashboard (if needed)

## Configuration

The demo reads configuration from `../client/config.env`. Key variables include:

- Contract IDs (REGISTRY_ID, UTILITIES_ID)
- Account secrets (for deriving public keys)
- Lease IDs (LEAF_ID, ROOT_ID)
- Demo parameters (UNIT, PERIOD)

## Mock Data

The demo uses mocked transaction outputs that match the format of the actual scripts:

- **Transaction hashes**: 64-character hex strings
- **Account addresses**: Derived from secret keys in config
- **Transaction timing**: Simulated processing delays
- **Explorer links**: Stellar testnet explorer URLs

## API Endpoints

- `GET /` - Main demo interface
- `POST /api/pay-rent` - Payment and activation demo
- `POST /api/post-reading` - Utility reading demo
- `POST /api/split-utilities` - Cost splitting demo
- `POST /api/mark-delinquent` - Delinquency demo

## Project Structure

```
web-demo/
├── api/
│   ├── index.py         # Flask app and API routes
│   └── demo_runner.py   # Mock script execution
├── static/
│   ├── style.css        # Styling
│   └── script.js        # Frontend logic
├── templates/
│   └── index.html       # Demo UI
├── requirements.txt     # Python dependencies
├── vercel.json         # Vercel configuration
└── README.md           # This file
```

## Usage

1. Click "Run Demo" on each step to execute that part of the workflow
2. Use "Run All Steps" to execute the complete demo sequentially
3. Click "Reset Demo" to clear all results and start over
4. Click on transaction hashes to view them on Stellar Explorer

## Notes

- This is a demonstration with mocked blockchain data
- No real transactions are executed
- Transaction hashes are randomly generated for realism
- Config is loaded from the parent `client/config.env` file
- All amounts, IDs, and addresses use your actual configuration

## Related Files

- `../client/scripts/demo_pay_rent.py` - Actual payment demo
- `../client/scripts/demo_post_reading.py` - Actual reading demo
- `../client/scripts/demo_split_utilities.py` - Actual split demo
- `../client/scripts/demo_mark_delinquent.py` - Actual delinquency demo

