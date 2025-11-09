#!/usr/bin/env python3
"""
Add Interactive Charts to Dashboard
Creates multiple charts for data visualization
"""

import pickle
import gspread
from pathlib import Path

# Configuration
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
TOKEN_FILE = Path("token.pickle")

print("📊 Adding Interactive Charts to Dashboard...")
print("=" * 60)

# Authenticate
with open(TOKEN_FILE, 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SPREADSHEET_ID)
dashboard = ss.worksheet('Dashboard')

print("✅ Connected to Dashboard sheet")

# Find where the trend data starts (search for "24-HOUR GENERATION TREND")
all_values = dashboard.get_all_values()
trend_start_row = None
for i, row in enumerate(all_values):
    if row and "24-HOUR GENERATION TREND" in str(row[0]):
        trend_start_row = i + 2  # +2 for header row
        break

if not trend_start_row:
    print("❌ Could not find trend data section")
    exit(1)

print(f"📍 Found trend data at row {trend_start_row}")

# Calculate data range (assuming 48 settlement periods typical)
trend_end_row = min(trend_start_row + 50, dashboard.row_count)

print(f"📊 Creating charts using data range: A{trend_start_row}:F{trend_end_row}")

# Note: Charts will overlay existing ones if any
# Manual removal needed via Google Sheets UI if desired

# Chart 1: Generation Mix Line Chart
print("\n📈 Creating Generation Mix Line Chart...")
chart1_spec = {
    "basicChart": {
        "chartType": "LINE",
        "legendPosition": "RIGHT_LEGEND",
        "axis": [
            {
                "position": "BOTTOM_AXIS",
                "title": "Settlement Period"
            },
            {
                "position": "LEFT_AXIS",
                "title": "Generation (MW)"
            }
        ],
        "domains": [
            {
                "domain": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 0,
                                "endColumnIndex": 1
                            }
                        ]
                    }
                }
            }
        ],
        "series": [
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 1,
                                "endColumnIndex": 2
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            },
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 2,
                                "endColumnIndex": 3
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            },
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 3,
                                "endColumnIndex": 4
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            },
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 4,
                                "endColumnIndex": 5
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            }
        ],
        "headerCount": 1
    },
    "title": "24-Hour Generation Trend by Source",
    "position": {
        "overlayPosition": {
            "anchorCell": {
                "sheetId": dashboard.id,
                "rowIndex": 0,
                "columnIndex": 7  # Column H
            }
        }
    }
}

# Chart 2: Renewable vs Fossil Pie Chart (based on generation mix)
print("📈 Creating Renewable vs Fossil Pie Chart...")
chart2_spec = {
    "pieChart": {
        "legendPosition": "RIGHT_LEGEND",
        "domain": {
            "sourceRange": {
                "sources": [
                    {
                        "sheetId": dashboard.id,
                        "startRowIndex": 10,  # Start of generation mix table
                        "endRowIndex": 25,     # ~15 fuel types
                        "startColumnIndex": 0,
                        "endColumnIndex": 1
                    }
                ]
            }
        },
        "series": {
            "sourceRange": {
                "sources": [
                    {
                        "sheetId": dashboard.id,
                        "startRowIndex": 10,
                        "endRowIndex": 25,
                        "startColumnIndex": 1,
                        "endColumnIndex": 2
                    }
                ]
            }
        }
    },
    "title": "Current Generation Mix by Fuel Type",
    "position": {
        "overlayPosition": {
            "anchorCell": {
                "sheetId": dashboard.id,
                "rowIndex": 0,
                "columnIndex": 16  # Column Q
            }
        }
    }
}

# Chart 3: Total Generation Area Chart
print("📈 Creating Total Generation Area Chart...")
chart3_spec = {
    "basicChart": {
        "chartType": "AREA",
        "legendPosition": "BOTTOM_LEGEND",
        "stackedType": "STACKED",
        "axis": [
            {
                "position": "BOTTOM_AXIS",
                "title": "Time"
            },
            {
                "position": "LEFT_AXIS",
                "title": "Generation (MW)"
            }
        ],
        "domains": [
            {
                "domain": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 0,
                                "endColumnIndex": 1
                            }
                        ]
                    }
                }
            }
        ],
        "series": [
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 1,
                                "endColumnIndex": 2
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            },
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 3,
                                "endColumnIndex": 4
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            },
            {
                "series": {
                    "sourceRange": {
                        "sources": [
                            {
                                "sheetId": dashboard.id,
                                "startRowIndex": trend_start_row - 1,
                                "endRowIndex": trend_end_row,
                                "startColumnIndex": 4,
                                "endColumnIndex": 5
                            }
                        ]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            }
        ],
        "headerCount": 1
    },
    "title": "Stacked Generation by Source (24h)",
    "position": {
        "overlayPosition": {
            "anchorCell": {
                "sheetId": dashboard.id,
                "rowIndex": 25,
                "columnIndex": 7  # Column H, below first chart
            }
        }
    }
}

# Create charts using batch update
print("\n🚀 Adding charts to dashboard...")
requests = [
    {"addChart": {"chart": chart1_spec}},
    {"addChart": {"chart": chart2_spec}},
    {"addChart": {"chart": chart3_spec}}
]

try:
    response = ss.batch_update({"requests": requests})
    print(f"✅ Successfully added {len(requests)} charts!")
except Exception as e:
    print(f"❌ Error adding charts: {e}")
    print("\n💡 Tip: You can manually create charts using:")
    print(f"   • Data range: A{trend_start_row}:F{trend_end_row}")
    print("   • Chart types: Line, Pie, Area")
    print("   • X-axis: Settlement Period (Column A)")
    print("   • Series: Wind, Solar, Nuclear, Gas, Total")
    exit(1)

print(f"\n✅ Dashboard Enhancement Complete!")
print(f"\n📊 Created Charts:")
print("   1. ⚡ 24-Hour Generation Trend (Line Chart)")
print("   2. 🥧 Current Generation Mix (Pie Chart)")
print("   3. 📊 Stacked Generation by Source (Area Chart)")

print(f"\n🔗 View Dashboard:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard.id}")

print(f"\n🔄 Auto-Update:")
print("   Run: python3 enhance_dashboard_layout.py")
print("   Cron: */5 * * * * cd '{}' && python3 enhance_dashboard_layout.py >> logs/dashboard_enhance.log 2>&1".format(Path.cwd()))
