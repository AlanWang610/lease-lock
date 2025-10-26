// Demo state management
const demoState = {
    paymentComplete: false,
    lockUnlocked: false,
    lockCode: null,
    currentTab: 'payment'
};

// Tab switching
document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.getAttribute('data-tab');
            switchTab(tab);
        });
    });
    
    // Generate a random access code (would normally come from blockchain)
    demoState.lockCode = generateAccessCode();
});

function switchTab(tab) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    // Update header
    updateHeader(tab);
    
    demoState.currentTab = tab;
}

function updateHeader(tab) {
    const titles = {
        payment: { title: 'Payment & Rent', subtitle: 'Pay rent and activate your lease' },
        utilities: { title: 'Utilities', subtitle: 'Post readings and split costs' },
        'smart-lock': { title: 'Smart Lock', subtitle: 'Access code and lock status' },
        delinquency: { title: 'Manage Status', subtitle: 'View and update lease status' }
    };
    
    const info = titles[tab] || titles.payment;
    document.getElementById('pageTitle').textContent = info.title;
    document.getElementById('pageSubtitle').textContent = info.subtitle;
}

function generateAccessCode() {
    // Generate an 8-digit code (normally from blockchain)
    return Math.floor(10000000 + Math.random() * 90000000).toString();
}

function showCode() {
    const codeDisplay = document.getElementById('codeDisplay');
    const btnShowCode = document.getElementById('btnShowCode');
    
    if (codeDisplay.textContent === '••••••••') {
        codeDisplay.textContent = demoState.lockCode;
        codeDisplay.style.letterSpacing = 'normal';
        btnShowCode.textContent = 'Hide Code';
    } else {
        codeDisplay.textContent = '••••••••';
        codeDisplay.style.letterSpacing = '8px';
        btnShowCode.textContent = 'Show Access Code';
    }
}

function unlockDoor() {
    const lockIcon = document.getElementById('lockIcon');
    const lockStatus = document.getElementById('lockStatus');
    const lockMessage = document.getElementById('lockMessage');
    const lockHistory = document.getElementById('lockHistory');
    const lockCodeSection = document.getElementById('lockCodeSection');
    
    lockIcon.textContent = '🔓';
    lockIcon.classList.add('unlocked');
    lockStatus.textContent = 'UNLOCKED';
    lockStatus.style.color = '#10b981';
    lockMessage.textContent = 'Lease activated • Access granted';
    lockMessage.style.color = '#10b981';
    lockHistory.textContent = `Unlocked at ${new Date().toLocaleTimeString()} • Activated via payment`;
    lockCodeSection.style.display = 'block';
    
    demoState.lockUnlocked = true;
}

function lockDoor() {
    const lockIcon = document.getElementById('lockIcon');
    const lockStatus = document.getElementById('lockStatus');
    const lockMessage = document.getElementById('lockMessage');
    const lockHistory = document.getElementById('lockHistory');
    
    lockIcon.textContent = '🔒';
    lockIcon.classList.remove('unlocked');
    lockStatus.textContent = 'LOCKED';
    lockStatus.style.color = '#ef4444';
    lockMessage.textContent = 'Lease delinquent • Access revoked';
    lockMessage.style.color = '#ef4444';
    lockHistory.textContent = `Locked at ${new Date().toLocaleTimeString()} • Marked as delinquent`;
    
    demoState.lockUnlocked = false;
}

// Run payment demo
async function runPayRent() {
    const btn = document.getElementById('btnPay');
    const result = document.getElementById('resultPayment');
    const leaseStatus = document.getElementById('leaseStatus');
    
    btn.disabled = true;
    btn.textContent = 'Processing Payment...';
    result.innerHTML = '<div class="loading">⏳ Processing payment and activating lease...</div>';
    
    try {
        const response = await fetch('/api/pay-rent', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="result-success">';
            html += '<h3>✓ Payment & Activation Complete</h3>';
            
            data.steps.forEach((step, idx) => {
                html += `<div class="transaction-detail">`;
                html += `<strong>${step.name}:</strong><br>`;
                html += `Transaction: <code>${step.tx_hash}</code><br>`;
                if (step.from) html += `From: <code>${step.from}</code><br>`;
                if (step.to) html += `To: <code>${step.to}</code><br>`;
                if (step.amount) html += `Amount: ${step.amount}<br>`;
                if (step.lease_id) html += `Lease ID: ${step.lease_id}<br>`;
                if (step.lock_status) html += `Lock: <strong>${step.lock_status}</strong><br>`;
                html += `<a href="${step.explorer_url}" target="_blank">🔗 View Transaction</a>`;
                html += `</div>`;
                
                if (step.lock_status === 'UNLOCKED') {
                    unlockDoor();
                    leaseStatus.textContent = 'Active';
                    leaseStatus.className = 'status-badge active';
                }
            });
            
            html += '</div>';
            if (data.note) {
                html += `<p style="color: #f59e0b; margin-top: 10px;">${data.note}</p>`;
            }
            html += '</div>';
            result.innerHTML = html;
            demoState.paymentComplete = true;
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Pay Rent & Activate';
}

// Run post reading demo
async function runPostReading() {
    const btn = document.getElementById('btnPostReading');
    const result = document.getElementById('resultReading');
    
    btn.disabled = true;
    btn.textContent = 'Posting Reading...';
    result.innerHTML = '<div class="loading">⏳ Posting utility reading to blockchain...</div>';
    
    try {
        const response = await fetch('/api/post-reading', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="result-success">';
            html += '<h3>✓ Utility Reading Posted</h3>';
            html += `<div class="transaction-detail">`;
            html += `<strong>Unit:</strong> ${data.unit}<br>`;
            html += `<strong>Period:</strong> ${data.period}<br>`;
            html += `<strong>Electricity:</strong> ${data.readings.electricity}<br>`;
            html += `<strong>Gas:</strong> ${data.readings.gas}<br>`;
            html += `<strong>Water:</strong> ${data.readings.water}<br>`;
            html += `Transaction: <code>${data.tx_hash}</code><br>`;
            html += `<a href="${data.explorer_url}" target="_blank">🔗 View Transaction</a>`;
            html += `</div></div>`;
            
            result.innerHTML = html;
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Post Reading to Blockchain';
}

// Run split utilities demo
async function runSplitUtilities() {
    const btn = document.getElementById('btnSplit');
    const result = document.getElementById('resultSplit');
    
    btn.disabled = true;
    btn.textContent = 'Calculating...';
    result.innerHTML = '<div class="loading">⏳ Calculating cost split...</div>';
    
    try {
        const response = await fetch('/api/split-utilities', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="result-success">';
            html += '<h3>✓ Utility Costs Calculated</h3>';
            html += `<div class="transaction-detail">`;
            html += `<strong>Period:</strong> ${data.period}<br>`;
            html += `<strong>Unit:</strong> ${data.unit}<br>`;
            html += `<strong>Active Leases:</strong> ${data.active_leases}<br><br>`;
            html += `<strong>Total Usage:</strong> ${data.total_usage.electricity}, ${data.total_usage.gas}, ${data.total_usage.water}<br><br>`;
            html += `<strong>Cost Breakdown (per lease):</strong><br>`;
            html += `  • Electricity: ${data.breakdown.electricity}<br>`;
            html += `  • Gas: ${data.breakdown.gas}<br>`;
            html += `  • Water: ${data.breakdown.water}<br>`;
            html += `<strong>Total per lease: ${data.per_lease_cost}</strong>`;
            html += `</div></div>`;
            
            result.innerHTML = html;
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Calculate Cost Split';
}

// Run mark delinquent demo
async function runMarkDelinquent() {
    const btn = document.getElementById('btnDelinquent');
    const result = document.getElementById('resultDelinquent');
    const leaseStatus = document.getElementById('leaseStatus');
    
    btn.disabled = true;
    btn.textContent = 'Processing...';
    result.innerHTML = '<div class="loading">⏳ Marking lease as delinquent...</div>';
    
    try {
        const response = await fetch('/api/mark-delinquent', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            let html = '<div class="result-success">';
            html += '<h3>✓ Lease Marked as Delinquent</h3>';
            html += `<div class="transaction-detail">`;
            html += `<strong>Lease ID:</strong> ${data.lease_id}<br>`;
            html += `<strong>Status:</strong> <span style="color: #ef4444;">${data.status.toUpperCase()}</span><br>`;
            html += `<strong>Lock Status:</strong> <strong>${data.lock_status}</strong><br>`;
            html += `Transaction: <code>${data.tx_hash}</code><br>`;
            html += `<a href="${data.explorer_url}" target="_blank">🔗 View Transaction</a>`;
            html += `</div></div>`;
            
            result.innerHTML = html;
            lockDoor();
            leaseStatus.textContent = 'Delinquent';
            leaseStatus.className = 'status-badge locked';
        }
    } catch (error) {
        result.innerHTML = `<div class="result-error">Error: ${error.message}</div>`;
    }
    
    btn.disabled = false;
    btn.textContent = 'Mark Lease as Delinquent';
}

function resetAll() {
    if (confirm('Reset all demo state? This will clear all results and lock status.')) {
        // Reset state
        demoState.paymentComplete = false;
        demoState.lockUnlocked = false;
        
        // Reset UI
        document.querySelectorAll('.result-panel').forEach(panel => {
            panel.innerHTML = '';
        });
        
        // Reset buttons
        document.querySelectorAll('.btn-primary').forEach(btn => {
            btn.disabled = false;
        });
        
        // Reset lease status
        document.getElementById('leaseStatus').textContent = 'Pending';
        document.getElementById('leaseStatus').className = 'status-badge pending';
        
        // Reset lock
        lockDoor();
        document.getElementById('lockCodeSection').style.display = 'none';
        
        alert('Demo reset!');
    }
}
