#!/usr/bin/env python3
from datetime import datetime, timedelta

# Current progress
files_processed = 375
total_files = 138909
remaining_files = total_files - files_processed

# Recent speed (from last entry)
seconds_per_file = 27.43  # Latest estimate from log

# Calculate time estimates
total_seconds = remaining_files * seconds_per_file
total_hours = total_seconds / 3600
total_days = total_hours / 24

# With 16 workers, but they seem to be processing serially
# based on the log showing individual file processing

print("⏱️  EXTRACTION COMPLETION ESTIMATE")
print("=" * 70)
print(f"\n📊 Current Progress:")
print(f"   Files processed: {files_processed:,}")
print(f"   Total files: {total_files:,}")
print(f"   Remaining: {remaining_files:,}")
print(f"   Progress: {(files_processed/total_files*100):.2f}%")

print(f"\n🚀 Current Speed:")
print(f"   ~{seconds_per_file:.1f} seconds per file")
print(f"   ~{3600/seconds_per_file:.1f} files per hour")
print(f"   ~{(3600/seconds_per_file)*24:.0f} files per day")

print(f"\n⏰ Time Estimates (at current speed):")
print(f"   Total time remaining: {total_hours:,.1f} hours")
print(f"   That's: {total_days:.1f} days")
print(f"   Or approximately: {total_days/7:.1f} weeks")

# Calculate completion date
completion_date = datetime.now() + timedelta(seconds=total_seconds)
print(f"\n📅 Estimated Completion:")
print(f"   {completion_date.strftime('%A, %B %d, %Y at %H:%M')}")

# Speed analysis from the log
print(f"\n📈 Speed Variation Observed:")
print(f"   Fastest: 13.56 s/file  (~265 files/hour)")
print(f"   Slowest: 145.62 s/file (~25 files/hour)")
print(f"   Current: {seconds_per_file} s/file  (~{3600/seconds_per_file:.0f} files/hour)")
print(f"   Average impact on estimate: ±50% variation")

# Alternative scenarios
print(f"\n🎯 Alternative Scenarios:")

# Best case (fastest observed speed)
best_speed = 13.56
best_hours = (remaining_files * best_speed) / 3600
best_days = best_hours / 24
print(f"\n   BEST CASE (13.56 s/file):")
print(f"   └─ {best_days:.1f} days (~{best_days/7:.1f} weeks)")

# Worst case (slowest observed speed)
worst_speed = 145.62
worst_hours = (remaining_files * worst_speed) / 3600
worst_days = worst_hours / 24
print(f"\n   WORST CASE (145.62 s/file):")
print(f"   └─ {worst_days:.1f} days (~{worst_days/7:.1f} weeks)")

# Realistic average (middle of range)
avg_speed = 40  # More realistic sustained average
avg_hours = (remaining_files * avg_speed) / 3600
avg_days = avg_hours / 24
print(f"\n   REALISTIC (40 s/file average):")
print(f"   └─ {avg_days:.1f} days (~{avg_days/7:.1f} weeks)")

print("\n" + "=" * 70)
print("💡 Note: Speed varies by file size and complexity.")
print("   Large PDFs take longer to process than small spreadsheets.")
print("=" * 70)
