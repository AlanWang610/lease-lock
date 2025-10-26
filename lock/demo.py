#!/usr/bin/env python3
"""
Complete Demo Script for Lease-Lock System

This script demonstrates the complete flow:
1. Deploy the updated lease registry contract
2. Start the lock daemon
3. Trigger lease events
4. Observe lock state changes

Usage:
    python demo.py
"""

import os
import sys
import subprocess
import time
import threading
from typing import Optional


class LeaseLockDemo:
    def __init__(self):
        self.contract_id = None
        self.unit = "unit:NYC:123-A"
        self.daemon_process = None

    def run_command(self, cmd: list, capture: bool = True) -> Optional[str]:
        """Run a command and return output if capture=True"""
        try:
            if capture:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            else:
                subprocess.run(cmd, check=True)
                return "OK"
        except subprocess.CalledProcessError as e:
            print(f"Error running command {' '.join(cmd)}: {e}")
            if capture and e.stderr:
                print(f"stderr: {e.stderr}")
            return None
        except FileNotFoundError:
            print(f"Error: Command not found: {cmd[0]}")
            return None

    def check_prerequisites(self) -> bool:
        """Check if all required tools are available"""
        print("Checking prerequisites...")
        
        # Check for stellar CLI
        if not self.run_command(["stellar", "--version"]):
            print("❌ Stellar CLI not found. Please install it first.")
            return False
        
        # Check for Python dependencies
        try:
            import requests
            print("✓ Python dependencies available")
        except ImportError:
            print("❌ Missing Python dependencies. Run: pip install -r requirements.txt")
            return False
        
        print("✓ All prerequisites met")
        return True

    def deploy_contract(self) -> bool:
        """Deploy the updated lease registry contract"""
        print("\n=== Deploying Updated Contract ===")
        
        # Build the contract
        print("Building contract...")
        if not self.run_command(["cargo", "build", "--release", "--target", "wasm32-unknown-unknown"], capture=False):
            print("❌ Failed to build contract")
            return False
        
        # Install the contract
        print("Installing contract...")
        output = self.run_command([
            "stellar", "contract", "install",
            "--wasm", "target/wasm32-unknown-unknown/release/lease_registry.wasm"
        ])
        
        if not output:
            print("❌ Failed to install contract")
            return False
        
        self.contract_id = output
        print(f"✓ Contract installed with ID: {self.contract_id}")
        
        # Deploy the contract
        print("Deploying contract...")
        deploy_output = self.run_command([
            "stellar", "contract", "deploy",
            "--id", self.contract_id
        ])
        
        if not deploy_output:
            print("❌ Failed to deploy contract")
            return False
        
        print(f"✓ Contract deployed successfully")
        return True

    def start_daemon(self) -> bool:
        """Start the lock daemon in a separate process"""
        print("\n=== Starting Lock Daemon ===")
        
        # Set environment variables
        env = os.environ.copy()
        env["LEASE_REGISTRY_ID"] = self.contract_id
        
        try:
            self.daemon_process = subprocess.Popen(
                [sys.executable, "iot_lock_daemon.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Give daemon time to start
            time.sleep(2)
            
            if self.daemon_process.poll() is None:
                print("✓ Lock daemon started successfully")
                return True
            else:
                print("❌ Lock daemon failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting daemon: {e}")
            return False

    def monitor_daemon_output(self):
        """Monitor daemon output in a separate thread"""
        if not self.daemon_process:
            return
        
        try:
            for line in iter(self.daemon_process.stdout.readline, ''):
                if line:
                    print(f"[DAEMON] {line.strip()}")
        except Exception as e:
            print(f"Error monitoring daemon: {e}")

    def trigger_events(self) -> bool:
        """Trigger lease events to test the daemon"""
        print("\n=== Triggering Lease Events ===")
        
        # Get tenant address
        tenant = self.run_command(["stellar", "keys", "address", "tenant"])
        if not tenant:
            print("❌ Could not get tenant address")
            return False
        
        print(f"Using tenant address: {tenant}")
        
        # Sequence of events
        events = [
            ("Activating lease", ["activate_lease", "--unit", self.unit, "--subtenant", tenant]),
            ("Marking as delinquent", ["set_delinquent", "--unit", self.unit, "--subtenant", tenant]),
            ("Reactivating lease", ["activate_lease", "--unit", self.unit, "--subtenant", tenant]),
            ("Ending lease", ["end_lease", "--unit", self.unit, "--subtenant", tenant])
        ]
        
        for description, args in events:
            print(f"\n{description}...")
            
            cmd = ["stellar", "contract", "invoke", "--id", self.contract_id, "--"] + args
            output = self.run_command(cmd)
            
            if output:
                print(f"✓ {description} successful")
                time.sleep(3)  # Wait for daemon to process
            else:
                print(f"❌ {description} failed")
        
        return True

    def cleanup(self):
        """Clean up resources"""
        if self.daemon_process:
            print("\nStopping daemon...")
            self.daemon_process.terminate()
            try:
                self.daemon_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.daemon_process.kill()
            print("✓ Daemon stopped")

    def run_demo(self) -> bool:
        """Run the complete demo"""
        print("=== Lease-Lock System Demo ===")
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Deploy contract
            if not self.deploy_contract():
                return False
            
            # Start daemon
            if not self.start_daemon():
                return False
            
            # Start monitoring daemon output
            monitor_thread = threading.Thread(target=self.monitor_daemon_output, daemon=True)
            monitor_thread.start()
            
            # Wait a bit for daemon to initialize
            time.sleep(3)
            
            # Trigger events
            if not self.trigger_events():
                return False
            
            print("\n=== Demo Complete ===")
            print("The lock daemon should have shown state changes:")
            print("- LOCKED -> UNLOCKED (lease activated)")
            print("- UNLOCKED -> LOCKED (marked delinquent)")
            print("- LOCKED -> UNLOCKED (lease reactivated)")
            print("- UNLOCKED -> LOCKED (lease ended)")
            
            # Keep daemon running for a bit to see final state
            print("\nKeeping daemon running for 10 seconds...")
            time.sleep(10)
            
            return True
            
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            return False
        finally:
            self.cleanup()


def main():
    """Entry point"""
    demo = LeaseLockDemo()
    success = demo.run_demo()
    
    if success:
        print("\n✓ Demo completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Demo failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
