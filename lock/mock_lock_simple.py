#!/usr/bin/env python3
"""
Simple Mock Lock Interface

This provides a basic terminal-based mock lock that shows lock state changes.
No fancy graphics, just simple text output to demonstrate the lock functionality.
"""

import time
from typing import Dict, Any, Optional


class MockLock:
    def __init__(self):
        self.locks: Dict[str, Dict[str, Any]] = {}
        self.running = False
    
    def update_state(self, unit: str, state: str, event_info: Dict[str, Any]) -> None:
        """Update the lock state for a unit"""
        self.locks[unit] = {
            "state": state,
            "last_event": event_info,
            "updated_at": time.time()
        }
        
        # Print simple status update
        status_symbol = "[UNLOCKED]" if state == "UNLOCKED" else "[LOCKED]"
        print(f"{status_symbol} LOCK STATUS: {unit} = {state}")
        
        if event_info:
            print(f"   Event: {event_info.get('type', 'Unknown')}")
            print(f"   Tenant: {event_info.get('who', 'Unknown')}")
    
    def get_state(self, unit: str) -> Optional[str]:
        """Get the current state of a lock"""
        return self.locks.get(unit, {}).get("state")
    
    def list_all_locks(self) -> Dict[str, str]:
        """Get all lock states"""
        return {unit: data["state"] for unit, data in self.locks.items()}
    
    def start(self) -> None:
        """Start the mock lock interface"""
        self.running = True
        print("Mock Lock Interface Started")
        print("=" * 40)
    
    def stop(self) -> None:
        """Stop the mock lock interface"""
        self.running = False
        print("=" * 40)
        print("Mock Lock Interface Stopped")
        
        # Show final status
        if self.locks:
            print("\nFinal Lock States:")
            for unit, data in self.locks.items():
                status_symbol = "[UNLOCKED]" if data["state"] == "UNLOCKED" else "[LOCKED]"
                print(f"  {status_symbol} {unit}: {data['state']}")


# Global mock lock instance
_mock_lock: Optional[MockLock] = None


def start_mock_lock() -> None:
    """Start the mock lock interface"""
    global _mock_lock
    _mock_lock = MockLock()
    _mock_lock.start()


def stop_mock_lock() -> None:
    """Stop the mock lock interface"""
    global _mock_lock
    if _mock_lock:
        _mock_lock.stop()
        _mock_lock = None


def update_lock_state(unit: str, state: str, event_info: Dict[str, Any]) -> None:
    """Update the lock state for a unit"""
    global _mock_lock
    if _mock_lock:
        _mock_lock.update_state(unit, state, event_info)


def get_lock_state(unit: str) -> Optional[str]:
    """Get the current state of a lock"""
    global _mock_lock
    if _mock_lock:
        return _mock_lock.get_state(unit)
    return None


def list_all_locks() -> Dict[str, str]:
    """Get all lock states"""
    global _mock_lock
    if _mock_lock:
        return _mock_lock.list_all_locks()
    return {}


if __name__ == "__main__":
    # Test the mock lock
    print("Testing Mock Lock Interface")
    print("=" * 30)
    
    start_mock_lock()
    
    # Simulate some events
    update_lock_state("NYC123", "UNLOCKED", {
        "type": "LeaseActivated",
        "who": "GDNJNBGFGUI2AFZOQEGGCF2VKTKXKCQLPY4JMBLH7ATH5CBKY3QRXLVU",
        "ts": "2024-01-15T10:30:00Z"
    })
    
    time.sleep(1)
    
    update_lock_state("NYC123", "LOCKED", {
        "type": "Delinquent",
        "who": "GDNJNBGFGUI2AFZOQEGGCF2VKTKXKCQLPY4JMBLH7ATH5CBKY3QRXLVU",
        "ts": "2024-01-15T10:35:00Z"
    })
    
    time.sleep(1)
    
    update_lock_state("NYC123", "UNLOCKED", {
        "type": "LeaseActivated",
        "who": "GDNJNBGFGUI2AFZOQEGGCF2VKTKXKCQLPY4JMBLH7ATH5CBKY3QRXLVU",
        "ts": "2024-01-15T10:40:00Z"
    })
    
    time.sleep(1)
    
    update_lock_state("NYC123", "LOCKED", {
        "type": "LeaseEnded",
        "who": "GDNJNBGFGUI2AFZOQEGGCF2VKTKXKCQLPY4JMBLH7ATH5CBKY3QRXLVU",
        "ts": "2024-01-15T10:45:00Z"
    })
    
    time.sleep(1)
    
    stop_mock_lock()
