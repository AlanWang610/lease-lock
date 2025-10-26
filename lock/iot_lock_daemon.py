#!/usr/bin/env python3
"""
IoT Lock Daemon for Lease-Lock Smart Contract

This daemon subscribes to lease registry contract events and manages a local lock state machine.
It polls the Stellar RPC for contract events and updates lock states based on lease events.

Events handled:
- LeaseActivated -> UNLOCK
- Delinquent or LeaseEnded -> LOCK
- SubleaseGranted -> no change (optional)

Usage:
    export LEASE_REGISTRY_ID=<your_contract_id>
    python iot_lock_daemon.py

Environment Variables:
    STELLAR_RPC: Stellar RPC endpoint (default: https://soroban-testnet.stellar.org)
    LEASE_REGISTRY_ID: Contract ID to monitor (required)
    LOCK_STATE_FILE: File to persist lock states (default: .lock_state.json)
    LOCK_CURSOR_FILE: File to persist event cursor (default: .lock_cursor.txt)
"""

import json
import time
import requests
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Import the mock lock
try:
    from mock_lock_simple import update_lock_state, start_mock_lock, stop_mock_lock
    MOCK_LOCK_AVAILABLE = True
except ImportError:
    MOCK_LOCK_AVAILABLE = False
    print("Mock lock not available - running in console mode only")


class LockDaemon:
    def __init__(self):
        self.rpc = os.getenv("STELLAR_RPC", "https://soroban-testnet.stellar.org")
        self.contract_id = os.getenv("LEASE_REGISTRY_ID")
        self.state_file = os.getenv("LOCK_STATE_FILE", ".lock_state.json")
        self.cursor_file = os.getenv("LOCK_CURSOR_FILE", ".lock_cursor.txt")
        
        # Lock states: lease_id -> {"state": "LOCKED"|"UNLOCKED", "last_event": {...}}
        self.locks: Dict[str, Dict[str, Any]] = {}
        
        if not self.contract_id:
            print("Error: LEASE_REGISTRY_ID environment variable is required")
            sys.exit(1)

    def load_state(self) -> None:
        """Load lock states from persistent storage"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.locks.update(json.load(f))
                print(f"Loaded {len(self.locks)} lock states from {self.state_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load state file {self.state_file}: {e}")

    def save_state(self) -> None:
        """Save lock states to persistent storage"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.locks, f, indent=2)
        except IOError as e:
            print(f"Error: Could not save state file {self.state_file}: {e}")

    def get_cursor(self) -> Optional[str]:
        """Get the last processed event cursor"""
        if os.path.exists(self.cursor_file):
            try:
                with open(self.cursor_file, 'r') as f:
                    cursor = f.read().strip()
                    return cursor if cursor else None
            except IOError as e:
                print(f"Warning: Could not read cursor file {self.cursor_file}: {e}")
        return None

    def put_cursor(self, cursor: Optional[str]) -> None:
        """Save the event cursor for resumption"""
        try:
            with open(self.cursor_file, 'w') as f:
                f.write(cursor or "")
        except IOError as e:
            print(f"Error: Could not save cursor file {self.cursor_file}: {e}")

    def apply_event(self, lease_id: str, ev_type: str, who: str, ts: str, event_id: str) -> None:
        """Apply an event to update lock state"""
        prev_state = self.locks.get(lease_id, {"state": "LOCKED"})
        
        # Determine new state based on event type
        # Contract emits "Activated" and "Delinq" events
        if ev_type == "Activated":
            new_state = "UNLOCKED"
        elif ev_type == "Delinq":
            new_state = "LOCKED"
        elif ev_type in ("Delinquent", "LeaseEnded", "LeaseActivated"):  # Legacy compatibility
            if ev_type == "LeaseActivated":
                new_state = "UNLOCKED"
            else:
                new_state = "LOCKED"
        elif ev_type == "SubleaseGranted":
            # Optional: no state change for sublease granted
            return
        else:
            # Unknown event type, ignore
            return
        
        # Update lock state
        self.locks[lease_id] = {
            "state": new_state,
            "last_event": {
                "type": ev_type,
                "who": who,
                "ts": ts,
                "id": event_id
            }
        }
        
        # Save state immediately
        self.save_state()
        
        # Log state change
        timestamp = datetime.utcnow().isoformat() + "Z"
        print(f"[{timestamp}] lease_id={lease_id}: {prev_state['state']} -> {new_state} ({ev_type})")
        
        # Update mock lock if available
        if MOCK_LOCK_AVAILABLE:
            event_info = {
                "type": ev_type,
                "who": who,
                "ts": ts,
                "id": event_id
            }
            update_lock_state(lease_id, new_state, event_info)

    def fetch_events(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Fetch events from Stellar RPC"""
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getEvents",
            "params": {
                "filters": [{
                    "type": "contract",
                    "contractIds": [self.contract_id],
                }],
                "limit": 50
            }
        }
        
        # Add cursor or start ledger
        if cursor:
            body["params"]["pagination"] = {"cursor": cursor}
        else:
            # Start from a recent ledger to avoid huge scans on first run
            # Use a recent ledger number (must be positive)
            # Using a large number to get recent events
            body["params"]["startLedger"] = 100000000
        
        try:
            response = requests.post(self.rpc, json=body, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching events: {e}")
            return {"error": str(e)}

    def parse_event(self, item: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
        """Parse event data from RPC response"""
        # Extract event type from topics
        topics = item.get("topic", []) or item.get("topics", [])
        topic_texts = item.get("topicText", [])
        
        # Event type is typically the first topic
        ev_type = "Unknown"
        if topic_texts and len(topic_texts) > 0:
            ev_type = topic_texts[0]
        elif topics and len(topics) > 0:
            ev_type = str(topics[0])
        
        # Lease ID (or unit) is typically the second topic for Activated/Delinq events
        lease_id = "unknown"
        if topic_texts and len(topic_texts) > 1:
            lease_id = topic_texts[1]
        elif topics and len(topics) > 1:
            lease_id = str(topics[1])
        
        # Address is in the value field
        value = item.get("value", {})
        who = value.get("address") or value.get("valueText") or "G..."
        
        # Timestamp and ID
        ts = item.get("ts", "")
        event_id = item.get("pagingToken") or item.get("id", "")
        
        return lease_id, ev_type, who, ts, event_id

    def run(self) -> None:
        """Main daemon loop"""
        print("Lock daemon started. Press Ctrl+C to stop.")
        print(f"Monitoring contract: {self.contract_id}")
        print(f"RPC endpoint: {self.rpc}")
        
        # Start mock lock if available
        if MOCK_LOCK_AVAILABLE:
            print("Starting mock lock interface...")
            start_mock_lock()
            time.sleep(1)  # Give mock lock time to initialize
        
        cursor = self.get_cursor()
        if cursor:
            print(f"Resuming from cursor: {cursor}")
        else:
            print("Starting fresh - will fetch recent events")
        
        try:
            while True:
                try:
                    # Fetch events
                    response = self.fetch_events(cursor)
                    
                    if "error" in response:
                        print(f"RPC error: {response['error']}")
                        time.sleep(5)
                        continue
                    
                    result = response.get("result", {})
                    events = result.get("events", [])
                    
                    # Process events
                    for event in events:
                        lease_id, ev_type, who, ts, event_id = self.parse_event(event)
                        self.apply_event(lease_id, ev_type, who, ts, event_id)
                    
                    # Update cursor
                    next_cursor = result.get("cursor")
                    if next_cursor:
                        self.put_cursor(next_cursor)
                        cursor = next_cursor
                    
                    # Sleep before next poll
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    print("\nShutting down gracefully...")
                    break
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    time.sleep(2)
                    
        except KeyboardInterrupt:
            print("\nExiting.")
        finally:
            # Stop mock lock if running
            if MOCK_LOCK_AVAILABLE:
                stop_mock_lock()
        
        print("Lock daemon stopped.")


def main():
    """Entry point"""
    daemon = LockDaemon()
    daemon.load_state()
    daemon.run()


if __name__ == "__main__":
    main()
