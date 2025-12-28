#!/usr/bin/env python3
"""
Real-time Pipeline Monitor
Displays parallel processing performance metrics
"""

import os
import time
import psutil
from datetime import datetime
from typing import Dict, List

def get_cpu_usage() -> Dict:
    """Get CPU usage per core"""
    return {
        'overall': psutil.cpu_percent(interval=1),
        'per_core': psutil.cpu_percent(interval=1, percpu=True),
        'count': psutil.cpu_count(),
        'load_avg': os.getloadavg()
    }

def get_memory_usage() -> Dict:
    """Get memory usage"""
    mem = psutil.virtual_memory()
    return {
        'total_gb': mem.total / (1024**3),
        'used_gb': mem.used / (1024**3),
        'available_gb': mem.available / (1024**3),
        'percent': mem.percent
    }

def get_python_processes() -> List[Dict]:
    """Get Python process details"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                processes.append({
                    'pid': proc.info['pid'],
                    'cpu': proc.info['cpu_percent'],
                    'mem': proc.info['memory_percent'],
                    'cmd': ' '.join(proc.info['cmdline'][:3]) if proc.info['cmdline'] else ''
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes

def display_dashboard():
    """Display real-time monitoring dashboard"""
    os.system('clear')

    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║         Dell R630 Pipeline Monitor - 32 Core Performance             ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # CPU Usage
    cpu = get_cpu_usage()
    print(f"🖥️  CPU Usage: {cpu['overall']:.1f}% overall")
    print(f"   Load Average: {cpu['load_avg'][0]:.2f}, {cpu['load_avg'][1]:.2f}, {cpu['load_avg'][2]:.2f}")

    # Show cores in 4 rows of 8
    print("\n   Core Usage:")
    for i in range(0, 32, 8):
        cores = cpu['per_core'][i:i+8]
        core_str = "   " + " ".join([f"{i+j:2d}:{c:5.1f}%" for j, c in enumerate(cores)])
        print(core_str)

    # Memory
    mem = get_memory_usage()
    print(f"\n💾 Memory: {mem['used_gb']:.1f} / {mem['total_gb']:.1f} GB ({mem['percent']:.1f}% used)")
    print(f"   Available: {mem['available_gb']:.1f} GB")

    # Python processes
    procs = get_python_processes()
    if procs:
        print(f"\n🐍 Python Processes ({len(procs)}):")
        # Sort by CPU usage
        procs_sorted = sorted(procs, key=lambda x: x['cpu'], reverse=True)[:10]
        for p in procs_sorted:
            if p['cpu'] > 0.1:  # Only show active processes
                print(f"   PID {p['pid']:6d}: CPU {p['cpu']:5.1f}%  MEM {p['mem']:5.1f}%  {p['cmd'][:50]}")

    print("\n" + "─" * 73)
    print("Press Ctrl+C to exit")

def main():
    """Main monitoring loop"""
    try:
        while True:
            display_dashboard()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped")

if __name__ == '__main__':
    main()
