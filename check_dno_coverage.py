#!/usr/bin/env python3
"""
Check DNO coverage in generator data
"""

import json

# Load generator data
with open('generators.json', 'r') as f:
    generators = json.load(f)

print('📊 Generator Coverage by DNO\n')
print('='*90)

# Group by DNO
dno_stats = {}
for gen in generators:
    dno = gen.get('dno', 'Unknown')
    if dno not in dno_stats:
        dno_stats[dno] = {'count': 0, 'capacity': 0}
    dno_stats[dno]['count'] += 1
    dno_stats[dno]['capacity'] += gen.get('capacity', 0)

# Sort by capacity
sorted_dnos = sorted(dno_stats.items(), key=lambda x: x[1]['capacity'], reverse=True)

print(f"{'DNO Name':<55} {'Generators':<12} {'Capacity (MW)':<15} {'%':<6}")
print('-'*90)

total_capacity = sum(stats['capacity'] for _, stats in sorted_dnos)
total_count = sum(stats['count'] for _, stats in sorted_dnos)

for dno, stats in sorted_dnos:
    pct = (stats['capacity'] / total_capacity * 100) if total_capacity > 0 else 0
    print(f"{dno:<55} {stats['count']:>10,}  {stats['capacity']:>13,.1f}  {pct:>5.1f}%")

print('-'*90)
print(f"{'TOTAL':<55} {total_count:>10,}  {total_capacity:>13,.1f}  100.0%")
print()
print(f'✅ Total DNOs represented: {len(dno_stats)}')
print()

# Now check against the 14 official DNOs
print('\n🔍 Checking against 14 Official GB DNO License Areas:\n')
print('='*90)

official_dnos = {
    'Eastern Power Networks (EPN)': 'UKPN - East England',
    'London Power Networks (LPN)': 'UKPN - London',
    'South Eastern Power Networks (SPN)': 'UKPN - South East England',
    'National Grid Electricity Distribution (East Midlands) Plc': 'NGED - East Midlands',
    'National Grid Electricity Distribution (West Midlands) Plc': 'NGED - West Midlands',
    'National Grid Electricity Distribution (South Wales) Plc': 'NGED - South Wales',
    'National Grid Electricity Distribution (South West) Plc': 'NGED - South West England',
    'SCOTTISH HYDRO ELECTRIC POWER DISTRIBUTION PLC': 'SSEN - Northern Scotland',
    'SOUTHERN ELECTRIC POWER DISTRIBUTION PLC': 'SSEN - Southern England',
    'Northern Powergrid (Yorkshire) plc': 'Northern Powergrid - Yorkshire',
    'Northern Powergrid (Northeast) plc': 'Northern Powergrid - Northeast',
    'ELECTRICITY NORTH WEST LIMITED': 'Electricity North West',
    'SP Distribution Ltd': 'SP Energy Networks - South Scotland',
    'SP Manweb plc': 'SP Energy Networks - Merseyside/North Wales'
}

print(f"{'Expected DNO':<60} {'Found?':<10}")
print('-'*90)

found_count = 0
for official_name, friendly_name in official_dnos.items():
    # Check if we have this DNO in our data
    found = official_name in dno_stats
    status = '✅ YES' if found else '❌ NO'
    print(f"{friendly_name:<60} {status:<10}")
    if found:
        found_count += 1
        print(f"  → {dno_stats[official_name]['count']:,} generators, {dno_stats[official_name]['capacity']:,.1f} MW")

print('-'*90)
print(f"Coverage: {found_count}/14 DNOs found ({found_count/14*100:.1f}%)")
