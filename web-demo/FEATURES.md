# Dashboard Features

## Overview

The Lease-Lock Dashboard is a modern, tab-based interface that demonstrates the complete lease-lock workflow with an interactive smart lock component.

## Main Features

### 🎨 Dashboard Design
- **Sidebar Navigation**: Clean, professional sidebar with tab icons
- **Tab-Based Interface**: Organized into logical sections
- **Responsive Layout**: Works on desktop and mobile devices
- **Modern UI**: Card-based design with smooth transitions

### 💳 Payment & Rent Tab
- **Lease Information Display**: Shows property unit, rent amount, lease ID, and status
- **Payment Processing**: Execute rent payment and activation
- **Transaction Details**: Full transaction hash with Stellar explorer link
- **Status Tracking**: Real-time lease status updates

### ⚡ Utilities Tab
- **Post Readings**: Record utility meter readings to blockchain
- **Display Usage**: Shows electricity, gas, and water consumption
- **Cost Split Calculation**: Automatically calculates per-lease costs
- **Oracle Integration**: Connects to Stellar blockchain oracle

### 🔐 Smart Lock Tab
- **Visual Lock Display**: Shows lock/unlock status with animated icon
- **Access Code Generator**: Generates unique 8-digit code after payment
- **Code Reveal**: Show/hide access code functionality
- **Lock History**: Displays last activity and status changes
- **Interactive States**: Locked/Unlocked visual feedback

### ⚠️ Manage Status Tab
- **Delinquency Management**: Mark lease as delinquent
- **Transaction History**: View all blockchain transactions
- **Lock Control**: Automatically locks door on delinquency
- **Warning System**: Clear visual warnings for destructive actions

## Interactive Features

### Smart Lock Integration
1. **Initial State**: Locked, requires payment
2. **After Payment**: Automatically unlocks with access code
3. **Code Access**: 
   - Shows 8-digit code
   - Can reveal/hide code
   - Only works when lease is active
4. **Delinquency**: Automatically locks when marked delinquent

### Tab Switching
- Smooth transitions between sections
- Persists state across tabs
- Updates header dynamically
- Maintains visual consistency

### Transaction Display
- Transaction hashes (64-char hex)
- Stellar explorer links
- Account addresses (shortened format)
- Operation details
- Status indicators

## User Flow

### Complete Workflow
1. **Start**: Land on Payment tab (lease is locked)
2. **Pay Rent**: Execute payment → activates lease
3. **Unlock**: Door automatically unlocks, receive access code
4. **Utilities**: Switch to Utilities tab, post readings
5. **Split Costs**: Calculate cost allocation
6. **Smart Lock**: View lock status and access code
7. **Delinquency**: (Optional) Test delinquency workflow

### Code Generation
The access code is a unique 8-digit number generated after successful payment. In production:
- Generated on blockchain after activation
- Cryptographically secure
- Unique per lease
- Automatically invalidates on delinquency or expiry

## Technical Details

### Data Flow
- **Mock Execution**: All operations use mocked blockchain calls
- **Realistic Hashes**: Transaction hashes use actual 64-char hex format
- **Account Addresses**: Derived from secrets in config
- **Config Integration**: Loads from `../client/config.env`

### State Management
- **Payment State**: Tracks completion status
- **Lock State**: Maintains lock/unlock status
- **Code State**: Stores generated access code
- **Tab State**: Current active tab

### Styling
- **Gradient Theme**: Purple gradient for primary actions
- **Status Colors**: 
  - Green for success/active
  - Yellow for pending
  - Red for locked/delinquent
- **Hover Effects**: Smooth transitions on interactions
- **Responsive Grid**: Adapts to screen size

## Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ JavaScript features
- CSS Grid and Flexbox
- No external dependencies

## Future Enhancements
- Real blockchain integration (optional)
- Multiple lock support
- Notification system
- Dark mode toggle
- Transaction export
- PDF receipt generation

