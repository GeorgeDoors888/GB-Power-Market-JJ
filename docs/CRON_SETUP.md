# 🔄 Set Up Automatic Map Updates

## Quick Start

Your maps are already embedded in the Dashboard! Now set up automatic updates:

```bash
# Edit your cron jobs
crontab -e

# Add ONE of these lines (choose your schedule):

# Option 1: Every 6 hours
0 */6 * * * /Users/georgemajor/GB\ Power\ Market\ JJ/cron_update_maps.sh

# Option 2: Daily at 6 AM
0 6 * * * /Users/georgemajor/GB\ Power\ Market\ JJ/cron_update_maps.sh

# Option 3: Every hour during trading (7 AM - 7 PM)
0 7-19 * * * /Users/georgemajor/GB\ Power\ Market\ JJ/cron_update_maps.sh

# Save and exit (in vi: press ESC, type :wq, press ENTER)
```

## Verify It's Working

```bash
# List current cron jobs
crontab -l

# Check logs (after first run)
tail -f "/Users/georgemajor/GB Power Market JJ/logs/map_updates_$(date +%Y%m%d).log"

# Test manually before cron
cd "/Users/georgemajor/GB Power Market JJ"
./cron_update_maps.sh
```

## What Gets Updated

- **Generators Map** (J20): 500 SVA generators with coordinates
- **GSP Regions** (J36): 14 DNO groups with capacity totals
- **Transmission Zones** (J52): Top 10 boundaries with real-time generation

## URLs of Your Maps

**Drive Links** (updated automatically):
- Generators: https://drive.google.com/uc?id=1z2_U9xm_kOG7wnQibZybtrq5akWwkgko
- GSP Regions: https://drive.google.com/uc?id=17TKRWnL_6e7gWu6d27O4XFVbe8K8HEmj
- Transmission: https://drive.google.com/uc?id=1nAOV9B-kxSqCWsuBaXOWPGteBVAVz7jm

**Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

## Manual Update Anytime

```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 auto_update_maps.py
```

---

**Setup Status**: ✅ Complete  
**Next Step**: Add cron job above (takes 30 seconds)
