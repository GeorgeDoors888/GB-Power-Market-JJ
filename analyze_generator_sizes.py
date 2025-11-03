#!/usr/bin/env python3
"""
Analyze generator size distribution
"""

import json

# Load generator data
with open('generators.json', 'r') as f:
    generators = json.load(f)

print('📊 Generator Size Analysis\n')
print('='*90)

# Get all capacities
capacities = [gen['capacity'] for gen in generators if gen.get('capacity', 0) > 0]
capacities_all = [gen['capacity'] for gen in generators]

print(f"Total generators: {len(generators):,}")
print(f"Generators with capacity > 0: {len(capacities):,}")
print(f"Generators with 0 capacity: {len(generators) - len(capacities):,}")
print()

# Find min and max
min_cap = min(capacities) if capacities else 0
max_cap = max(capacities) if capacities else 0
avg_cap = sum(capacities) / len(capacities) if capacities else 0
median_cap = sorted(capacities)[len(capacities)//2] if capacities else 0

print('📈 CAPACITY STATISTICS')
print('-'*90)
print(f"Minimum capacity:  {min_cap:>12.6f} MW")
print(f"Maximum capacity:  {max_cap:>12,.2f} MW")
print(f"Average capacity:  {avg_cap:>12,.2f} MW")
print(f"Median capacity:   {median_cap:>12,.2f} MW")
print(f"Total capacity:    {sum(capacities):>12,.2f} MW")
print()

# Find the smallest generators
print('🔬 SMALLEST GENERATORS (Top 20)')
print('-'*90)
smallest = sorted(generators, key=lambda x: x.get('capacity', 0))[:20]
print(f"{'Rank':<6} {'Capacity (MW)':<15} {'Type':<20} {'Name':<50}")
print('-'*90)
for i, gen in enumerate(smallest, 1):
    if gen.get('capacity', 0) > 0:
        print(f"{i:<6} {gen['capacity']:<15.6f} {gen['type']:<20} {gen['name'][:47]:<50}")

print()
print('🏭 LARGEST GENERATORS (Top 20)')
print('-'*90)
largest = sorted(generators, key=lambda x: x.get('capacity', 0), reverse=True)[:20]
print(f"{'Rank':<6} {'Capacity (MW)':<15} {'Type':<20} {'Name':<50}")
print('-'*90)
for i, gen in enumerate(largest, 1):
    print(f"{i:<6} {gen['capacity']:<15,.2f} {gen['type']:<20} {gen['name'][:47]:<50}")

print()
print('📊 SIZE DISTRIBUTION')
print('-'*90)

# Size categories
size_ranges = [
    (0, 0.1, '< 100 kW'),
    (0.1, 1, '100 kW - 1 MW'),
    (1, 5, '1 - 5 MW'),
    (5, 10, '5 - 10 MW'),
    (10, 50, '10 - 50 MW'),
    (50, 100, '50 - 100 MW'),
    (100, 500, '100 - 500 MW'),
    (500, 1000, '500 MW - 1 GW'),
    (1000, 10000, '> 1 GW')
]

print(f"{'Size Range':<20} {'Count':<12} {'Total Capacity (MW)':<20} {'% of Total':<12}")
print('-'*90)

total_capacity = sum(capacities)
for min_size, max_size, label in size_ranges:
    in_range = [g for g in generators if min_size <= g.get('capacity', 0) < max_size]
    range_capacity = sum(g['capacity'] for g in in_range)
    pct = (range_capacity / total_capacity * 100) if total_capacity > 0 else 0
    if len(in_range) > 0:
        print(f"{label:<20} {len(in_range):>10,}  {range_capacity:>18,.2f}  {pct:>10.1f}%")

print('-'*90)
print(f"{'TOTAL':<20} {len(capacities):>10,}  {total_capacity:>18,.2f}  {100.0:>10.1f}%")
print()

# By energy type
print('⚡ SIZE BY ENERGY TYPE')
print('-'*90)

type_stats = {}
for gen in generators:
    gen_type = gen.get('type', 'Unknown')
    capacity = gen.get('capacity', 0)
    if capacity > 0:
        if gen_type not in type_stats:
            type_stats[gen_type] = {'min': capacity, 'max': capacity, 'total': 0, 'count': 0}
        type_stats[gen_type]['min'] = min(type_stats[gen_type]['min'], capacity)
        type_stats[gen_type]['max'] = max(type_stats[gen_type]['max'], capacity)
        type_stats[gen_type]['total'] += capacity
        type_stats[gen_type]['count'] += 1

print(f"{'Type':<25} {'Count':<10} {'Min (MW)':<15} {'Max (MW)':<15} {'Avg (MW)':<15}")
print('-'*90)

for gen_type, stats in sorted(type_stats.items(), key=lambda x: x[1]['total'], reverse=True):
    avg = stats['total'] / stats['count']
    print(f"{gen_type:<25} {stats['count']:>8,}  {stats['min']:>13.3f}  {stats['max']:>13,.2f}  {avg:>13,.2f}")

print()
print('✅ Analysis complete!')
