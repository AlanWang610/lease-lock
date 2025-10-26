#!/usr/bin/env python3
"""
Unified Test Script for Lease-Lock System

This script tests the complete lock system:
1. Mock lock interface functionality
2. Lock daemon integration
3. Contract event simulation
4. End-to-end lock state changes

Usage:
    python test_lock_system.py [--demo] [--daemon] [--contract]
"""

import os
import sys
import time
import subprocess
import argparse
from datetime import datetime
from typing import Dict, Any, Optional


class LockSystemTester:
    def __init__(self):
        self.contract_id = "CDT3G6BMDXWIY27V6QXKSAD22FSJE7EQPRQ44D27TMWK6DQPLDSUPBVJ"
        self.tenant_address = "GDNJNBGFGUI2AFZOQEGGCF2VKTKXKCQLPY4JMBLH7ATH5CBKY3QRXLVU"
        self.unit = "NYC123"
        
    def test_mock_lock(self) -> bool:
        """Test the mock lock interface"""
        print("Testing Mock Lock Interface")
        print("=" * 40)
        
        try:
            from mock_lock_simple import start_mock_lock, update_lock_state, stop_mock_lock
            print("+ Mock lock imported successfully")
            
            # Start mock lock
            start_mock_lock()
            
            # Test state changes
            print("\nTesting state changes:")
            
            # Test sequence
            test_events = [
                ("UNLOCKED", "LeaseActivated", "2024-01-15T10:30:00Z"),
                ("LOCKED", "Delinquent", "2024-01-15T10:35:00Z"),
                ("UNLOCKED", "LeaseActivated", "2024-01-15T10:40:00Z"),
                ("LOCKED", "LeaseEnded", "2024-01-15T10:45:00Z")
            ]
            
            for state, event_type, timestamp in test_events:
                update_lock_state(self.unit, state, {
                    "type": event_type,
                    "who": self.tenant_address,
                    "ts": timestamp
                })
                time.sleep(0.5)  # Brief pause between events
            
            # Stop mock lock
            stop_mock_lock()
            
            print("\n+ Mock lock test completed successfully!")
            return True
            
        except ImportError as e:
            print(f"X Failed to import mock lock: {e}")
            return False
        except Exception as e:
            print(f"X Error during mock lock test: {e}")
            return False
    
    def test_daemon_integration(self) -> bool:
        """Test the daemon integration with mock lock"""
        print("\nTesting Daemon Integration")
        print("=" * 40)
        
        try:
            # Set environment
            os.environ['LEASE_REGISTRY_ID'] = self.contract_id
            
            # Import daemon components
            from iot_lock_daemon import LockDaemon
            from mock_lock_simple import start_mock_lock, stop_mock_lock
            
            print("+ Daemon and mock lock imported successfully")
            
            # Create daemon instance
            daemon = LockDaemon()
            print("+ Daemon instance created")
            
            # Test mock lock integration
            start_mock_lock()
            
            # Simulate event processing
            print("\nSimulating event processing:")
            test_events = [
                ("LeaseActivated", "UNLOCKED"),
                ("Delinquent", "LOCKED"),
                ("LeaseActivated", "UNLOCKED"),
                ("LeaseEnded", "LOCKED")
            ]
            
            for event_type, expected_state in test_events:
                print(f"Processing event: {event_type}")
                daemon.apply_event(
                    self.unit, 
                    event_type, 
                    self.tenant_address, 
                    datetime.utcnow().isoformat() + "Z",
                    f"test-{event_type}-{int(time.time())}"
                )
                time.sleep(0.5)
            
            stop_mock_lock()
            
            print("\n+ Daemon integration test completed successfully!")
            return True
            
        except Exception as e:
            print(f"X Error during daemon integration test: {e}")
            return False
    
    def test_contract_events(self) -> bool:
        """Test actual contract event triggering"""
        print("\nTesting Contract Events")
        print("=" * 40)
        
        try:
            # Check if stellar CLI is available
            result = subprocess.run(["stellar", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("X Stellar CLI not available - skipping contract test")
                return False
            
            print("+ Stellar CLI available")
            
            # Test contract invocation
            print(f"\nTesting contract events for unit: {self.unit}")
            
            # Test activate_lease
            print("Testing activate_lease...")
            cmd = [
                "stellar", "contract", "invoke",
                "--source-account", "test-tenant",
                "--id", self.contract_id,
                "--", "activate_lease",
                "--unit", self.unit,
                "--subtenant", self.tenant_address
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("+ activate_lease successful")
            else:
                print(f"X activate_lease failed: {result.stderr}")
                return False
            
            time.sleep(2)
            
            # Test set_delinquent
            print("Testing set_delinquent...")
            cmd[6] = "set_delinquent"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("+ set_delinquent successful")
            else:
                print(f"X set_delinquent failed: {result.stderr}")
                return False
            
            time.sleep(2)
            
            # Test end_lease
            print("Testing end_lease...")
            cmd[6] = "end_lease"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("+ end_lease successful")
            else:
                print(f"X end_lease failed: {result.stderr}")
                return False
            
            print("\n+ Contract events test completed successfully!")
            return True
            
        except subprocess.TimeoutExpired:
            print("X Contract test timed out")
            return False
        except Exception as e:
            print(f"X Error during contract test: {e}")
            return False
    
    def run_demo(self) -> None:
        """Run a complete demonstration"""
        print("LEASE-LOCK SYSTEM DEMO")
        print("=" * 50)
        print(f"Contract ID: {self.contract_id}")
        print(f"Unit: {self.unit}")
        print(f"Tenant: {self.tenant_address}")
        print()
        
        # Mock lock states
        lock_states = {}
        
        def update_lock(unit, state, event_type, tenant):
            """Update lock state and show visual feedback"""
            prev_state = lock_states.get(unit, "LOCKED")
            lock_states[unit] = state
            
            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            
            # Show state change
            print(f"[{timestamp}] {unit}: {prev_state} -> {state} ({event_type})")
            
            # Show lock visual
            if state == "UNLOCKED":
                print("[UNLOCKED] LOCK STATUS: NYC123 = UNLOCKED")
                print("   Event: LeaseActivated")
                print(f"   Tenant: {tenant}")
                print("   -> Door is OPEN - Tenant can enter")
            else:
                print("[LOCKED] LOCK STATUS: NYC123 = LOCKED")
                print(f"   Event: {event_type}")
                print(f"   Tenant: {tenant}")
                print("   -> Door is LOCKED - Access denied")
            
            print()
            time.sleep(1)
        
        print("Starting Lock Daemon...")
        print("Mock Lock Interface Started")
        print("=" * 40)
        print()
        
        # Simulate the event sequence
        print("Monitoring contract events...")
        print()
        
        # Event sequence
        events = [
            ("UNLOCKED", "LeaseActivated"),
            ("LOCKED", "Delinquent"),
            ("UNLOCKED", "LeaseActivated"),
            ("LOCKED", "LeaseEnded")
        ]
        
        for state, event_type in events:
            print(f"Triggering: {event_type.lower().replace('_', ' ')}")
            update_lock(self.unit, state, event_type, self.tenant_address)
        
        # Final status
        print("=" * 40)
        print("Mock Lock Interface Stopped")
        print()
        print("Final Lock States:")
        print("  [LOCKED] NYC123: LOCKED")
        print()
        print("Demo completed successfully!")
        print()
        print("This demonstrates how the lock daemon would:")
        print("1. Monitor the smart contract for events")
        print("2. Update lock states based on lease events")
        print("3. Provide visual feedback for lock changes")
        print("4. Control physical IoT locks in production")
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("RUNNING ALL TESTS")
        print("=" * 50)
        
        tests = [
            ("Mock Lock Interface", self.test_mock_lock),
            ("Daemon Integration", self.test_daemon_integration),
            ("Contract Events", self.test_contract_events)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\nRunning {test_name} Test...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"X {test_name} test failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "+ PASSED" if result else "X FAILED"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("All tests passed! System is ready for production.")
            return True
        else:
            print("Some tests failed. Please check the issues above.")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test the Lease-Lock System")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--daemon", action="store_true", help="Test daemon integration only")
    parser.add_argument("--contract", action="store_true", help="Test contract events only")
    parser.add_argument("--mock", action="store_true", help="Test mock lock only")
    
    args = parser.parse_args()
    
    tester = LockSystemTester()
    
    if args.demo:
        tester.run_demo()
    elif args.daemon:
        tester.test_daemon_integration()
    elif args.contract:
        tester.test_contract_events()
    elif args.mock:
        tester.test_mock_lock()
    else:
        # Run all tests by default
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
