# UK DNO DUoS Charging Methodology Collection - README

This collection of tools and guides helps you gather Distribution Use of System (DUoS) charging methodologies from all 14 UK Distribution Network Operators (DNOs).

## What's Included

1. **Comprehensive Guide**: `COMPLETE_UK_DNO_DUOS_CHARGING_GUIDE.md`
   - Detailed information about each DNO
   - Links to charging documents
   - Instructions for manual downloads

2. **Download Scripts**:
   - `download_all_dno_duos_files.py` - Attempts automated download (note: most files require manual download)
   - `manual_dno_download_helper.py` - Assists with manual downloads by opening websites

## Why Manual Downloads Are Required

DNO websites implement security measures to prevent automated downloads:
- CSRF protection
- Browser user-agent verification
- Anti-scraping mechanisms
- Session cookies requirements

## How to Use This Collection

### 1. Reviewing the Guide

Start by reviewing the comprehensive guide:
```bash
less COMPLETE_UK_DNO_DUOS_CHARGING_GUIDE.md
```

### 2. Using the Manual Download Helper

The helper script opens browser windows to relevant DNO pages:
```bash
source .venv/bin/activate && python manual_dno_download_helper.py
```

This interactive tool will:
- Display a menu of all UK DNOs
- Open your browser to the correct websites
- Provide instructions for finding the required documents

### 3. File Organization

Organize downloaded files in this structure:
```
duos_nged_data/
├── east_midlands/
├── west_midlands/
├── south_wales/
└── south_west/

duos_spm_data/

duos_ssen_data/
├── shepd/
└── sepd/

...etc
```

## DNO Coverage

This collection covers all 14 UK DNOs:

| DNO Code | Company | MPAN Region(s) |
|----------|---------|----------------|
| ENWL | Electricity North West | 16 |
| NPG | Northern Powergrid | 15, 23 |
| NGED | National Grid Electricity Distribution | 11, 14, 21, 22 |
| UKPN | UK Power Networks | 10, 12, 19 |
| SPEN | SP Energy Networks | 13, 18 |
| SSEN | Scottish and Southern Electricity Networks | 17, 20 |

## Key Documents To Download

For each DNO, the essential documents are:

1. **LC14 Charging Statement** - The formal regulatory document
2. **Schedule of Charges** - Detailed tariff tables
3. **CDCM Model** - The Common Distribution Charging Methodology calculation model

These documents provide full transparency on how DUoS charges are calculated and applied across the UK electricity distribution network.
