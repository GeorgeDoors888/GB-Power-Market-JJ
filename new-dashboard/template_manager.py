#!/usr/bin/env python3
"""
Template Manager - Detect changes and replicate to new sheets
Monitors Dashboard V2 as master template, applies changes to new deployments
"""

import json
import gspread
from google.oauth2 import service_account
from datetime import datetime
from pathlib import Path
import difflib

# Configuration
MASTER_SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'  # Dashboard V2
SA_FILE = Path(__file__).parent.parent / 'inner-cinema-credentials.json'
TEMPLATE_CACHE = Path(__file__).parent / 'template_cache.json'

class TemplateManager:
    def __init__(self):
        # Connect to Google Sheets
        creds = service_account.Credentials.from_service_account_file(
            str(SA_FILE),
            scopes=['https://www.googleapis.com/auth/spreadsheets', 
                    'https://www.googleapis.com/auth/drive']
        )
        self.gc = gspread.authorize(creds)
        self.master = self.gc.open_by_key(MASTER_SHEET_ID)
        
    def capture_template(self):
        """Capture current state of master template"""
        print("📸 Capturing template from Dashboard V2...")
        
        template = {
            'timestamp': datetime.now().isoformat(),
            'spreadsheet_id': MASTER_SHEET_ID,
            'sheets': {},
            'formatting': {},
            'structure': {}
        }
        
        # Capture each sheet's data and structure
        for sheet in self.master.worksheets():
            sheet_name = sheet.title
            print(f"   📄 Capturing {sheet_name}...")
            
            # Get all data
            data = sheet.get_all_values()
            
            # Get formatting info (rows, cols, frozen rows/cols)
            template['sheets'][sheet_name] = {
                'data': data,
                'rows': sheet.row_count,
                'cols': sheet.col_count,
                'frozen_rows': sheet.frozen_row_count,
                'frozen_cols': sheet.frozen_col_count
            }
            
            # Capture specific formatting for key sections
            if sheet_name == 'Dashboard':
                template['formatting']['header'] = {
                    'range': 'A1:K3',
                    'background': '#0072ce',
                    'font_color': '#FFFFFF'
                }
                template['formatting']['sections'] = {
                    'generation': 'A10',
                    'prices': 'A80',
                    'constraints': 'A116'
                }
        
        # Save template
        TEMPLATE_CACHE.write_text(json.dumps(template, indent=2))
        print(f"✅ Template saved to {TEMPLATE_CACHE}")
        print(f"   Captured {len(template['sheets'])} sheets")
        
        return template
    
    def detect_changes(self):
        """Compare current master with cached template"""
        print("🔍 Detecting changes in Dashboard V2...")
        
        if not TEMPLATE_CACHE.exists():
            print("⚠️  No cached template found. Run capture_template() first.")
            return None
        
        # Load cached template
        cached = json.loads(TEMPLATE_CACHE.read_text())
        
        # Get current state
        current = self.capture_template()
        
        changes = {
            'timestamp': datetime.now().isoformat(),
            'sheets_added': [],
            'sheets_removed': [],
            'sheets_modified': {}
        }
        
        # Detect sheet changes
        cached_sheets = set(cached['sheets'].keys())
        current_sheets = set(current['sheets'].keys())
        
        changes['sheets_added'] = list(current_sheets - cached_sheets)
        changes['sheets_removed'] = list(cached_sheets - current_sheets)
        
        # Detect data changes in existing sheets
        for sheet_name in cached_sheets & current_sheets:
            cached_data = cached['sheets'][sheet_name]['data']
            current_data = current['sheets'][sheet_name]['data']
            
            if cached_data != current_data:
                # Find specific cell changes
                diff = []
                for row_idx, (cached_row, current_row) in enumerate(zip(cached_data, current_data)):
                    for col_idx, (cached_cell, current_cell) in enumerate(zip(cached_row, current_row)):
                        if cached_cell != current_cell:
                            diff.append({
                                'row': row_idx + 1,
                                'col': col_idx + 1,
                                'old': cached_cell,
                                'new': current_cell
                            })
                
                if diff:
                    changes['sheets_modified'][sheet_name] = diff
        
        print("\n📊 Change Summary:")
        print(f"   Sheets added: {len(changes['sheets_added'])}")
        print(f"   Sheets removed: {len(changes['sheets_removed'])}")
        print(f"   Sheets modified: {len(changes['sheets_modified'])}")
        
        if changes['sheets_modified']:
            print("\n📝 Modified sheets:")
            for sheet_name, diff in changes['sheets_modified'].items():
                print(f"   {sheet_name}: {len(diff)} cells changed")
        
        return changes
    
    def apply_template(self, target_sheet_id, sheets_to_copy=None):
        """Apply template to a new spreadsheet"""
        print(f"📋 Applying template to {target_sheet_id}...")
        
        if not TEMPLATE_CACHE.exists():
            print("⚠️  No cached template. Capturing current state...")
            self.capture_template()
        
        template = json.loads(TEMPLATE_CACHE.read_text())
        target = self.gc.open_by_key(target_sheet_id)
        
        # If no specific sheets specified, copy all
        if sheets_to_copy is None:
            sheets_to_copy = list(template['sheets'].keys())
        
        for sheet_name in sheets_to_copy:
            if sheet_name not in template['sheets']:
                print(f"⚠️  Sheet '{sheet_name}' not in template, skipping")
                continue
            
            print(f"   📄 Applying {sheet_name}...")
            
            sheet_data = template['sheets'][sheet_name]
            
            # Create or get sheet
            try:
                target_sheet = target.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                target_sheet = target.add_worksheet(
                    title=sheet_name,
                    rows=sheet_data['rows'],
                    cols=sheet_data['cols']
                )
            
            # Copy data
            if sheet_data['data']:
                target_sheet.update('A1', sheet_data['data'])
            
            # Apply frozen rows/cols if any
            if sheet_data.get('frozen_rows', 0) > 0:
                target_sheet.freeze(rows=sheet_data['frozen_rows'])
            if sheet_data.get('frozen_cols', 0) > 0:
                target_sheet.freeze(cols=sheet_data['frozen_cols'])
            
            print(f"      ✅ {len(sheet_data['data'])} rows copied")
        
        # Apply formatting
        if 'Dashboard' in sheets_to_copy:
            print("   🎨 Applying formatting...")
            dashboard = target.worksheet('Dashboard')
            
            # Apply header formatting
            fmt = template['formatting']['header']
            header_range = dashboard.range(fmt['range'])
            for cell in header_range:
                cell.format = {
                    'backgroundColor': {'red': 0, 'green': 0.45, 'blue': 0.81},
                    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
                }
            dashboard.update_cells(header_range, value_input_option='RAW')
        
        print(f"✅ Template applied successfully!")
        return target
    
    def watch_changes(self, callback=None):
        """Watch for changes and trigger callback"""
        print("👀 Starting change detection...")
        print("   Ctrl+C to stop")
        
        try:
            import time
            while True:
                changes = self.detect_changes()
                
                if changes and (changes['sheets_added'] or 
                               changes['sheets_removed'] or 
                               changes['sheets_modified']):
                    print(f"\n⚡ Changes detected at {changes['timestamp']}")
                    
                    if callback:
                        callback(changes)
                
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n✅ Stopped watching")


def main():
    import sys
    
    manager = TemplateManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 template_manager.py capture              - Capture current template")
        print("  python3 template_manager.py detect               - Detect changes")
        print("  python3 template_manager.py apply <sheet_id>     - Apply template to new sheet")
        print("  python3 template_manager.py watch                - Watch for changes")
        return
    
    command = sys.argv[1]
    
    if command == 'capture':
        manager.capture_template()
    
    elif command == 'detect':
        changes = manager.detect_changes()
        if changes:
            print("\n💾 Changes saved for future replication")
    
    elif command == 'apply':
        if len(sys.argv) < 3:
            print("❌ Error: Provide target spreadsheet ID")
            return
        target_id = sys.argv[2]
        manager.apply_template(target_id)
    
    elif command == 'watch':
        manager.watch_changes()
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == '__main__':
    main()
