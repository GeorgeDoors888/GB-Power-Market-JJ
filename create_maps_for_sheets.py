#!/usr/bin/env python3
"""
GB Power Market - Maps for Google Sheets
=========================================
Creates static map images that can be embedded in Google Sheets using =IMAGE()
Also generates clickable links for interactive maps.
"""

import folium
from folium import plugins
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import subprocess
import os

# ============================================================================
# Configuration
# ============================================================================
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

UK_CENTER = [54.5, -3.5]

FUEL_COLORS = {
    'Wind': '#00a86b',
    'Solar': '#ffd700',
    'Nuclear': '#ff6b6b',
    'Gas': '#ffa500',
    'Coal': '#8b4513',
    'Hydro': '#4169e1',
    'Battery': '#9400d3',
    'Biomass': '#9acd32',
    'Other': '#808080'
}

# ============================================================================
# Data Loading
# ============================================================================

def load_sva_generators():
    """Load SVA generators with coordinates"""
    query = f"""
    SELECT 
        name as generator_name,
        technology,
        capacity_mw,
        gsp as gsp_group,
        lat as latitude,
        lng as longitude,
        fuel_type
    FROM `{PROJECT_ID}.{DATASET}.sva_generators_with_coords`
    WHERE lat IS NOT NULL 
      AND lng IS NOT NULL
      AND capacity_mw > 1  -- Only show generators > 1 MW for cleaner map
    LIMIT 2000  -- Limit for faster rendering in Sheets context
    """
    return bq_client.query(query).to_dataframe()


def load_gsp_summary():
    """Load GSP group summary"""
    query = f"""
    SELECT 
        gspgroupid as gsp_group,
        gspgroupname as gsp_name,
        COUNT(DISTINCT nationalgridbmunit) as num_generators,
        ROUND(SUM(generationcapacity), 0) as total_capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE gspgroupid IS NOT NULL
      AND generationcapacity > 0
    GROUP BY gspgroupid, gspgroupname
    ORDER BY total_capacity_mw DESC
    LIMIT 14  -- Top 14 GSP groups
    """
    return bq_client.query(query).to_dataframe()


def load_transmission_boundaries():
    """Load latest boundary generation"""
    query = f"""
    WITH latest AS (
        SELECT MAX(settlementDate) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
    )
    SELECT 
        boundary,
        ROUND(AVG(generation), 0) as avg_generation_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
    CROSS JOIN latest
    WHERE DATE(settlementDate) = DATE(latest.max_date)
      AND boundary != 'N'
    GROUP BY boundary
    ORDER BY avg_generation_mw DESC
    LIMIT 10  -- Top 10 boundaries
    """
    return bq_client.query(query).to_dataframe()


# ============================================================================
# Map Creation - Simplified for Sheets
# ============================================================================

def create_simple_generator_map(df, output_file='sheets_generators_map.html'):
    """Create simplified generator map suitable for Sheets viewing"""
    print(f"🗺️ Creating simplified generator map: {output_file}")
    
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB positron',
        width='100%',
        height='100%'
    )
    
    # Group by fuel type
    fuel_counts = df['fuel_type'].value_counts()
    
    for idx, gen in df.iterrows():
        if pd.notna(gen['latitude']) and pd.notna(gen['longitude']):
            fuel = gen['fuel_type'] if pd.notna(gen['fuel_type']) else 'Other'
            color = FUEL_COLORS.get(fuel, FUEL_COLORS['Other'])
            
            folium.CircleMarker(
                location=[gen['latitude'], gen['longitude']],
                radius=4,
                popup=f"<b>{gen['generator_name']}</b><br/>{gen['capacity_mw']:.1f} MW<br/>{fuel}",
                tooltip=f"{gen['generator_name']} ({gen['capacity_mw']:.1f} MW)",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
                weight=1
            ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; top: 10px; right: 10px; width: 150px;
                background-color: white; border: 2px solid grey; z-index: 9999;
                padding: 10px; font-size: 12px;">
    <h4 style="margin: 0 0 10px 0;">🔌 GB Generators</h4>
    <p style="margin: 0; font-size: 11px;">{count} generators shown<br/>
    Updated: {date}</p>
    </div>
    '''.format(count=len(df), date=datetime.now().strftime('%Y-%m-%d'))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save(output_file)
    print(f"✅ Saved: {output_file}")
    return output_file


def create_simple_gsp_map(df, output_file='sheets_gsp_regions_map.html'):
    """Create simplified GSP map"""
    print(f"🗺️ Creating GSP regions map: {output_file}")
    
    gsp_centers = {
        '_A': (51.5, -0.1, 'Eastern'),
        '_B': (52.5, 1.0, 'East Anglia'),
        '_C': (51.3, -0.8, 'South East'),
        '_D': (51.0, -1.3, 'Southern'),
        '_E': (50.8, -1.8, 'South Western'),
        '_F': (52.3, -1.5, 'West Midlands'),
        '_G': (52.8, -2.0, 'North West'),
        '_H': (54.0, -2.0, 'Cumbria'),
        '_J': (53.8, -1.5, 'Yorkshire'),
        '_K': (54.5, -1.5, 'North East'),
        '_L': (55.8, -4.2, 'South Scotland'),
        '_M': (56.5, -3.5, 'Mid Scotland'),
        '_N': (57.5, -4.0, 'North Scotland'),
        '_P': (51.5, -3.0, 'South Wales'),
    }
    
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB positron'
    )
    
    colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
              '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
              '#008080', '#e6beff', '#9a6324', '#fffac8']
    
    for idx, gsp in df.iterrows():
        gsp_id = gsp['gsp_group']
        if gsp_id in gsp_centers:
            lat, lon, region_name = gsp_centers[gsp_id]
            color = colors[idx % len(colors)]
            radius = min(max(gsp['total_capacity_mw'] / 500, 10), 35)
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=f"<b>GSP {gsp_id}</b><br/>{gsp['gsp_name']}<br/>{gsp['total_capacity_mw']:,.0f} MW<br/>{gsp['num_generators']} generators",
                tooltip=f"GSP {gsp_id}: {gsp['total_capacity_mw']:,.0f} MW",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
                weight=2
            ).add_to(m)
    
    legend_html = '''
    <div style="position: fixed; top: 10px; right: 10px; width: 180px;
                background-color: white; border: 2px solid grey; z-index: 9999;
                padding: 10px; font-size: 12px;">
    <h4 style="margin: 0 0 10px 0;">🗺️ GSP Regions</h4>
    <p style="margin: 0; font-size: 11px;">
    Total: {total:,.0f} MW<br/>
    {count} regions<br/>
    Updated: {date}
    </p>
    </div>
    '''.format(total=df['total_capacity_mw'].sum(), count=len(df), 
               date=datetime.now().strftime('%Y-%m-%d'))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save(output_file)
    print(f"✅ Saved: {output_file}")
    return output_file


def create_simple_boundary_map(df, output_file='sheets_transmission_map.html'):
    """Create simplified transmission boundary map"""
    print(f"🗺️ Creating transmission boundary map: {output_file}")
    
    boundary_centers = {
        'B1': (51.5, 0.5), 'B2': (51.3, -0.5), 'B3': (50.8, -1.1),
        'B4': (51.0, -2.5), 'B5': (52.5, -1.5), 'B6': (52.0, -2.5),
        'B7': (53.5, -1.5), 'B8': (53.0, -3.0), 'B9': (56.0, -4.0),
        'B10': (51.5, -3.5), 'B11': (54.5, -2.0), 'B12': (52.5, 1.0),
        'B13': (50.5, -4.0), 'B14': (54.0, -3.0), 'B15': (52.0, -0.5),
        'B16': (55.0, -1.5), 'B17': (53.0, -1.0),
    }
    
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB dark_matter'
    )
    
    max_gen = df['avg_generation_mw'].max()
    
    for idx, boundary in df.iterrows():
        b_id = boundary['boundary']
        if b_id in boundary_centers:
            lat, lon = boundary_centers[b_id]
            intensity = boundary['avg_generation_mw'] / max_gen
            
            if intensity > 0.7:
                color = '#ff0000'
            elif intensity > 0.4:
                color = '#ff6600'
            elif intensity > 0.2:
                color = '#ffcc00'
            else:
                color = '#00ff00'
            
            radius = min(max(boundary['avg_generation_mw'] / 500, 8), 40)
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=f"<b>Boundary {b_id}</b><br/>{boundary['avg_generation_mw']:,.0f} MW",
                tooltip=f"{b_id}: {boundary['avg_generation_mw']:,.0f} MW",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
    
    legend_html = '''
    <div style="position: fixed; top: 10px; right: 10px; width: 200px;
                background-color: white; border: 2px solid grey; z-index: 9999;
                padding: 10px; font-size: 12px;">
    <h4 style="margin: 0 0 10px 0;">⚡ Transmission Zones</h4>
    <p style="margin: 0; font-size: 10px;">
    🔴 High (>70%)<br/>
    🟠 Medium (40-70%)<br/>
    🟡 Low (20-40%)<br/>
    🟢 Very Low (<20%)<br/>
    Updated: {date}
    </p>
    </div>
    '''.format(date=datetime.now().strftime('%Y-%m-%d'))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save(output_file)
    print(f"✅ Saved: {output_file}")
    return output_file


# ============================================================================
# Screenshot Conversion (requires selenium/chrome)
# ============================================================================

def convert_to_png_via_screenshot(html_file, png_file):
    """Try to convert HTML to PNG using browser screenshot"""
    try:
        # Check if we have chrome/chromium
        chrome_path = None
        for path in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                     '/Applications/Chromium.app/Contents/MacOS/Chromium']:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if chrome_path:
            abs_html = os.path.abspath(html_file)
            abs_png = os.path.abspath(png_file)
            
            cmd = [
                chrome_path,
                '--headless',
                '--disable-gpu',
                '--screenshot=' + abs_png,
                '--window-size=1200,800',
                'file://' + abs_html
            ]
            
            print(f"   Converting {html_file} to {png_file}...")
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if os.path.exists(png_file):
                print(f"   ✅ Created: {png_file}")
                return True
            else:
                print(f"   ⚠️ Screenshot failed")
                return False
        else:
            print(f"   ℹ️ Chrome not found - skipping PNG conversion")
            return False
            
    except Exception as e:
        print(f"   ⚠️ PNG conversion failed: {e}")
        return False


# ============================================================================
# Sheets Integration Helper
# ============================================================================

def generate_sheets_formulas(map_files):
    """Generate Google Sheets formulas for embedding maps"""
    print("\n" + "=" * 80)
    print("📊 GOOGLE SHEETS INTEGRATION")
    print("=" * 80)
    
    print("\n📝 Copy these formulas into your Google Sheets:\n")
    
    # Option 1: Hyperlinks to interactive maps
    print("━━━ OPTION 1: Clickable Links to Interactive Maps ━━━")
    print("(Add these to your Dashboard sheet)")
    print()
    
    for name, file in map_files.items():
        # For local testing
        abs_path = os.path.abspath(file)
        print(f'=HYPERLINK("file://{abs_path}", "🗺️ {name}")')
    
    print()
    print("⚠️ Note: file:// links only work locally.")
    print("   For cloud access, upload HTML files to:")
    print("   • GitHub Pages (free)")
    print("   • Railway/Vercel static hosting")
    print("   • Google Cloud Storage with public access")
    print()
    
    # Option 2: Static images
    print("━━━ OPTION 2: Static Map Images (if PNG created) ━━━")
    print("(Upload PNG files to Google Drive, get shareable link, use IMAGE formula)")
    print()
    print('=IMAGE("https://drive.google.com/uc?id=YOUR_FILE_ID_HERE")')
    print()
    
    # Option 3: Data summary table
    print("━━━ OPTION 3: Data Summary (Always Available) ━━━")
    print("(Add map data directly to sheets)")
    print()


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("🗺️ GB POWER MARKET - MAPS FOR GOOGLE SHEETS")
    print("=" * 80)
    
    # Load data
    print("\n📊 Loading data from BigQuery...")
    sva_df = load_sva_generators()
    gsp_df = load_gsp_summary()
    boundary_df = load_transmission_boundaries()
    
    print(f"   • SVA Generators: {len(sva_df)}")
    print(f"   • GSP Groups: {len(gsp_df)}")
    print(f"   • Transmission Boundaries: {len(boundary_df)}")
    
    # Create simplified maps
    print("\n🎨 Creating simplified maps for Sheets...")
    map_files = {
        'Generators': create_simple_generator_map(sva_df),
        'GSP Regions': create_simple_gsp_map(gsp_df),
        'Transmission': create_simple_boundary_map(boundary_df)
    }
    
    # Try to create PNG versions
    print("\n📸 Attempting to create PNG images...")
    for name, html_file in map_files.items():
        png_file = html_file.replace('.html', '.png')
        convert_to_png_via_screenshot(html_file, png_file)
    
    # Generate Sheets integration guide
    generate_sheets_formulas(map_files)
    
    print("\n" + "=" * 80)
    print("✅ COMPLETE")
    print("=" * 80)
    print("\n📁 Files created:")
    for name, file in map_files.items():
        print(f"   • {file}")
        png = file.replace('.html', '.png')
        if os.path.exists(png):
            print(f"   • {png}")
    
    print("\n💡 Next steps:")
    print("   1. Open HTML files locally to test")
    print("   2. Upload to web hosting for cloud access")
    print("   3. Or upload PNG to Google Drive and use =IMAGE() in Sheets")


if __name__ == '__main__':
    main()
