const demoState = {
    paymentComplete: false,
    currentBid: 0,
    auctionWon: false,
    currentTab: 'auctions'
};

document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.getAttribute('data-tab');
            switchTab(tab);
        });
    });
});

function switchTab(tab) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    updateHeader(tab);
    demoState.currentTab = tab;
}

function updateHeader(tab) {
    const titles = {
        auctions: { title: 'Auctions', subtitle: 'Second-price auction listings' },
        payment: { title: 'Payments', subtitle: 'Lease payment and activation' },
        utilities: { title: 'Utilities', subtitle: 'Meter readings and cost allocation' }
    };
    
    const info = titles[tab] || titles.auctions;
    document.getElementById('pageTitle').textContent = info.title;
    document.getElementById('pageSubtitle').textContent = info.subtitle;
}

async function placeBid() {
    const bidInput = document.getElementById('bidAmount');
    const btn = document.getElementById('btnPlaceBid');
    const result = document.getElementById('resultAuction');
    const currentBidDisplay = document.getElementById('currentBid');
    
    const bidAmount = parseFloat(bidInput.value);
    
    if (!bidAmount || bidAmount < 3500) {
        alert('Minimum bid: 3,500 XLM');
        return;
    }
    
    btn.disabled = true;
    btn.textContent = 'Processing...';
    result.innerHTML = '<div class="loading">Placing bid on blockchain</div>';
    
    try {
        const response = await fetch('/api/place-bid', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: bidAmount })
        });
        
        const data = await response.json();
        
        if (data.success) {
            demoState.currentBid = bidAmount;
            currentBidDisplay.textContent = `${bidAmount.toLocaleString()} XLM`;
            
            let html = '<div class="result-success">';
            html += '<h3>Bid Placed</h3>';
            html += `<p>Amount: ${bidAmount.toLocaleString()} XLM</p>`;
            
            if (data.tx_hash) {
                html += `<p>Transaction: <code>${data.tx_hash}</code></p>`;
                html += `<a href="https://stellar.expert/explorer/testnet/tx/${data.tx_hash}" target="_blank">View Transaction</a>`;
            }
            
            html += '<p style="margin-top: 10px;"><strong>Second-Price Auction:</strong> Winner pays second-highest bid, not own bid amount.</p>';
            html += '<p style="margin-top: 10px;">Tokens escrowed in smart contract. Viewable on Stellar Expert.</p>';
            
            html += '</div>';
            result.innerHTML = html;
            demoState.auctionWon = true;
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Place Bid';
}

async function runPayRent() {
    const btn = document.getElementById('btnPay');
    const result = document.getElementById('resultPayment');
    const leaseStatus = document.getElementById('leaseStatus');
    
    btn.disabled = true;
    btn.textContent = 'Processing...';
    result.innerHTML = '<div class="loading">Executing payment transaction</div>';
    
    try {
        const response = await fetch('/api/pay-rent', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="result-success">';
            html += '<h3>Payment & Activation Complete</h3>';
            
            data.steps.forEach((step, idx) => {
                html += '<div class="transaction-detail">';
                html += `<strong>${step.name}:</strong><br>`;
                html += `Transaction: <code>${step.tx_hash}</code><br>`;
                if (step.from) html += `From: <code>${step.from}</code><br>`;
                if (step.to) html += `To: <code>${step.to}</code><br>`;
                if (step.amount) html += `Amount: ${step.amount}<br>`;
                if (step.lease_id) html += `Lease ID: ${step.lease_id}<br>`;
                if (step.lock_status) html += `Lock: <strong>${step.lock_status}</strong><br>`;
                html += `<a href="${step.explorer_url}" target="_blank">View Transaction</a>`;
                html += '</div>';
                
                if (step.lock_status === 'UNLOCKED') {
                    leaseStatus.textContent = 'Active';
                    leaseStatus.className = 'status-badge active';
                }
            });
            
            html += '</div>';
            if (data.note) {
                html += `<p style="color: #808080; margin-top: 10px;">${data.note}</p>`;
            }
            result.innerHTML = html;
            demoState.paymentComplete = true;
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Execute Payment & Activation';
}

async function fetchUtilities() {
    const btn = document.getElementById('btnFetchUtils');
    const result = document.getElementById('resultReading');
    
    btn.disabled = true;
    btn.textContent = 'Fetching...';
    result.innerHTML = '<div class="loading">Fetching utility readings from oracle</div>';
    
    try {
        const response = await fetch('/api/post-reading', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="result-success">';
            html += '<h3>Utility Readings Retrieved</h3>';
            html += '<div class="transaction-detail">';
            html += `<strong>Property:</strong> 285 Washington St, Somerville, MA 02143<br>`;
            html += `<strong>Period:</strong> ${data.period}<br>`;
            html += `<strong>Readings:</strong><br>`;
            html += `Electricity: ${data.readings.electricity}<br>`;
            html += `Gas: ${data.readings.gas}<br>`;
            html += `Water: ${data.readings.water}<br>`;
            html += `Transaction: <code>${data.tx_hash}</code><br>`;
            html += `<a href="${data.explorer_url}" target="_blank">View Transaction</a>`;
            html += '</div></div>';
            
            result.innerHTML = html;
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Fetch Readings';
}

async function calculateSplit() {
    const btn = document.getElementById('btnSplit');
    const result = document.getElementById('resultSplit');
    
    btn.disabled = true;
    btn.textContent = 'Calculating...';
    result.innerHTML = '<div class="loading">Calculating cost split</div>';
    
    try {
        const response = await fetch('/api/split-utilities', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="result-success">';
            html += '<h3>Cost Split Calculation</h3>';
            html += '<div class="transaction-detail">';
            html += `<strong>Period:</strong> ${data.period}<br>`;
            html += `<strong>Property:</strong> 285 Washington St, Somerville, MA 02143<br>`;
            html += `<strong>Active Leases Sharing:</strong> ${data.active_leases}<br><br>`;
            html += `<strong>Total Usage:</strong> ${data.total_usage.electricity}, ${data.total_usage.gas}, ${data.total_usage.water}<br><br>`;
            html += `<strong>Cost Breakdown:</strong><br>`;
            html += `Electricity: ${data.breakdown.electricity}<br>`;
            html += `Gas: ${data.breakdown.gas}<br>`;
            html += `Water: ${data.breakdown.water}<br>`;
            html += `<strong>Total per lease: ${data.per_lease_cost}</strong>`;
            html += '</div></div>';
            
            result.innerHTML = html;
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Calculate Cost Split';
}

function resetAll() {
    if (confirm('Reset all demo state?')) {
        location.reload();
    }
}
