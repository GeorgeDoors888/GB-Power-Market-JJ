#!/usr/bin/env python3
"""
Monitor UpCloud Server Health & Failover to Dell
Runs on Dell server, monitors UpCloud, activates backup services when UpCloud fails
"""

import requests
import subprocess
import time
from datetime import datetime
import logging
import os

logging.basicConfig(
    filename='failover_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

UPCLOUD_IP = '94.237.55.234'
UPCLOUD_HEALTH_ENDPOINT = f'http://{UPCLOUD_IP}:8080/health'
CHECK_INTERVAL = 60  # seconds
FAILURE_THRESHOLD = 3  # consecutive failures before failover

# Services to activate on Dell during failover
DELL_SERVICES = [
    'realtime_dashboard_updater.py',
    'gsp_auto_updater.py', 
    'update_dashboard_preserve_layout.py',
    'update_outages_enhanced.py'
]

class FailoverManager:
    def __init__(self):
        self.consecutive_failures = 0
        self.failover_active = False
        self.dell_processes = []
        self.work_dir = os.path.dirname(os.path.abspath(__file__))
    
    def check_upcloud_health(self):
        """Check if UpCloud server is responding"""
        try:
            # Check health endpoint
            response = requests.get(UPCLOUD_HEALTH_ENDPOINT, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Check if services are healthy
                if data.get('status') == 'healthy':
                    return True
            
            # Fallback: ping server
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', UPCLOUD_IP],
                capture_output=True
            )
            return result.returncode == 0
            
        except requests.RequestException:
            # Try ping as fallback
            try:
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', UPCLOUD_IP],
                    capture_output=True
                )
                return result.returncode == 0
            except:
                return False
    
    def activate_failover(self):
        """Start dashboard services on Dell"""
        if self.failover_active:
            return
        
        logging.warning("🚨 FAILOVER ACTIVATED - Starting Dell backup services")
        print("\n" + "="*60)
        print("🚨 FAILOVER ACTIVATED")
        print("="*60)
        print("UpCloud server unresponsive - Starting Dell backup services...")
        print()
        
        os.chdir(self.work_dir)
        
        for service in DELL_SERVICES:
            try:
                # Start service as background process with logging
                log_file = f'logs/failover_{service}.log'
                os.makedirs('logs', exist_ok=True)
                
                with open(log_file, 'a') as f:
                    proc = subprocess.Popen(
                        ['python3', service],
                        stdout=f,
                        stderr=subprocess.STDOUT
                    )
                
                self.dell_processes.append((service, proc))
                logging.info(f"✅ Started {service} on Dell (PID: {proc.pid})")
                print(f"  ✅ Started {service} (PID: {proc.pid})")
            except Exception as e:
                logging.error(f"❌ Failed to start {service}: {e}")
                print(f"  ❌ Failed to start {service}: {e}")
        
        self.failover_active = True
        print("\n✅ Dell backup services active")
        print("="*60 + "\n")
    
    def deactivate_failover(self):
        """Stop Dell services when UpCloud recovers"""
        if not self.failover_active:
            return
        
        logging.info("✅ UpCloud recovered - Stopping Dell backup services")
        print("\n" + "="*60)
        print("✅ UPCLOUD RECOVERED")
        print("="*60)
        print("Stopping Dell backup services...")
        print()
        
        for service, proc in self.dell_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                logging.info(f"✅ Stopped {service}")
                print(f"  ✅ Stopped {service}")
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                logging.warning(f"⚠️  Force killed {service}")
                print(f"  ⚠️  Force killed {service}")
            except Exception as e:
                logging.error(f"❌ Error stopping {service}: {e}")
        
        self.dell_processes = []
        self.failover_active = False
        print("\n✅ Normal operations resumed on UpCloud")
        print("="*60 + "\n")
    
    def run(self):
        """Main monitoring loop"""
        logging.info("🔍 Starting UpCloud health monitor...")
        print("="*60)
        print("🔍 UPCLOUD HEALTH MONITOR")
        print("="*60)
        print(f"Monitoring: {UPCLOUD_IP}")
        print(f"Check interval: {CHECK_INTERVAL}s")
        print(f"Failover threshold: {FAILURE_THRESHOLD} consecutive failures")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        while True:
            try:
                is_healthy = self.check_upcloud_health()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if is_healthy:
                    if self.consecutive_failures > 0:
                        logging.info(f"✅ UpCloud recovered after {self.consecutive_failures} failures")
                    
                    self.consecutive_failures = 0
                    
                    # Deactivate failover if it was active
                    if self.failover_active:
                        self.deactivate_failover()
                    
                    status = "✅ UpCloud healthy"
                    if self.failover_active:
                        status += " | 🔄 Failover ACTIVE"
                    print(f"[{timestamp}] {status}", end='\r')
                
                else:
                    self.consecutive_failures += 1
                    logging.warning(f"⚠️  UpCloud check failed ({self.consecutive_failures}/{FAILURE_THRESHOLD})")
                    print(f"[{timestamp}] ⚠️  UpCloud check failed ({self.consecutive_failures}/{FAILURE_THRESHOLD})    ")
                    
                    # Activate failover if threshold reached
                    if self.consecutive_failures >= FAILURE_THRESHOLD and not self.failover_active:
                        self.activate_failover()
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\n" + "="*60)
                print("🛑 Monitor stopped by user")
                print("="*60)
                if self.failover_active:
                    print("\n⚠️  Failover still active - cleaning up...")
                    self.deactivate_failover()
                print("\n✅ Monitor shutdown complete")
                break
            except Exception as e:
                logging.error(f"❌ Monitor error: {e}")
                print(f"\n❌ Error: {e}")
                time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    manager = FailoverManager()
    manager.run()
