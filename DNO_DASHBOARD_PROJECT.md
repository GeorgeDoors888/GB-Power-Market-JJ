# DNO Dashboard Project

**Status**: ✅ Phase 1 Complete  
**Last Updated**: 7 December 2025  
**Spreadsheet**: [BtM Dashboard](https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/)

---

## 🎯 Project Overview

Interactive DNO (Distribution Network Operator) mapping and analytics dashboard integrated with Google Sheets, featuring real UK DNO license area boundaries, postcode geocoding, and DUoS rate lookups.

### Core Features
- ✅ Real DNO geographic boundaries (14 regions, 5.6MB GeoJSON)
- ✅ Interactive Leaflet.js maps in Google Sheets
- ✅ Postcode → lat/lon geocoding (postcodes.io API)
- ✅ Battery site marker plotting
- ✅ DNO lookup and DUoS rate retrieval
- ✅ Automated clasp deployment

---

## 📁 Project Structure

```
GB-Power-Market-JJ/
├── Code.gs (465 lines)                           # Main Apps Script with 3 map functions
├── gb_power_map_deployment/
│   └── dno_regions.geojson (239,769 lines)      # Real DNO boundaries
├── revenue_comparison_clasp/                     # Clasp deployment directory
│   ├── .clasp.json                              # Script ID: 1zwDbH6rP98P...
│   ├── Code.gs                                  # Deployed version
│   └── appsscript.json                          # Manifest
├── dno_lookup_python.py                         # DNO/DUoS rate lookup
├── dno_webhook_server.py                        # Flask webhook for auto-refresh
├── bess_auto_trigger.gs                         # Apps Script button trigger
└── DNO_DASHBOARD_PROJECT.md                     # This file
```

---

## 🗺️ Map Features

### 1. Interactive DNO Map
**Menu**: `🗺️ DNO Map` → `View Interactive Map`

**Features**:
- 14 color-coded DNO regions
- Hover to see DNO name, MPAN ID, coverage
- Click regions to zoom
- Pan and zoom controls
- Real geographic boundaries from GeoJSON

**Data Source**: GitHub hosted GeoJSON  
**URL**: `https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/gb_power_map_deployment/dno_regions.geojson`

### 2. Map with Site Markers
**Menu**: `🗺️ DNO Map` → `View Map with Site Markers`

**Features**:
- All DNO boundaries (semi-transparent)
- Red circular marker for battery site location
- Auto-zoom to site (zoom level 10)
- Popup shows: postcode, area, lat/lon

**Data Source**: 
- Postcode from cell `BtM!A6`
- Geocoding via postcodes.io API (free)

### 3. Embedded Map
**Menu**: `🗺️ DNO Map` → `Embed Map in DNO Sheet`

**Features**:
- Static map reference in column H
- Google Drive hosted HTML
- Limited interactivity (Google Sheets IMAGE() limitation)

**Note**: Modal maps provide better UX

---

## 📊 DNO Data Structure

### GeoJSON Properties
```json
{
  "type": "Feature",
  "geometry": {
    "type": "MultiPolygon",
    "coordinates": [[[lon, lat], ...]]
  },
  "properties": {
    "dno_id": 10,
    "gsp_group": "_A",
    "dno_code": "UKPN",
    "dno_name": "UK Power Networks",
    "area": "East England",
    "mpan_id": 10,
    "area_sqkm": 20429.1,
    "coverage": "Norfolk Suffolk Essex..."
  }
}
```

### 14 UK DNO Regions (MPAN IDs)
- 10: UKPN East England
- 11: UKPN London
- 12: UKPN South East
- 13: WMID West Midlands
- 14: EMID East Midlands
- 15: EMID West Midlands
- 16: NGED West Midlands
- 17: NGED East Midlands
- 18: NGED South West
- 19: NGED South Wales
- 20: SSEN South
- 21: SSEN North
- 22: SPEN Merseyside & North Wales
- 23: SPEN Yorkshire

---

## 🎨 Color Scheme

Current 14-color palette (assigned by MPAN ID modulo):
```javascript
const colors = [
  '#FF6B6B',  // Red
  '#4ECDC4',  // Teal
  '#45B7D1',  // Blue
  '#FFA07A',  // Light salmon
  '#98D8C8',  // Mint
  '#F7DC6F',  // Yellow
  '#BB8FCE',  // Purple
  '#85C1E9',  // Sky blue
  '#F8B739',  // Orange
  '#52B788',  // Green
  '#E76F51',  // Coral
  '#2A9D8F',  // Dark teal
  '#264653',  // Navy
  '#E9C46A'   // Gold
];
```

---

## 🔧 Technical Stack

### Frontend
- **Leaflet.js** v1.9.4 - Interactive maps
- **OpenStreetMap** tiles - Base layer
- **HTML5/CSS3/JavaScript** - Map UI

### Backend
- **Google Apps Script** - Menu system & deployment
- **Python 3** - DNO lookup, webhook server
- **Flask** - Webhook endpoint (port 5001)
- **ngrok** - Expose webhook to internet

### APIs
- **postcodes.io** - Free UK postcode geocoding
- **BigQuery** - DNO reference data, DUoS rates
- **Google Sheets API** - Data updates via gspread

### Deployment
- **clasp** v3.1.3 - Automated Apps Script deployment
- **GitHub** - GeoJSON hosting & version control
- **Google Drive** - Embedded map HTML storage

---

## 🚀 Deployment

### Current Production Setup
- **Spreadsheet ID**: `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I`
- **Script ID**: `1zwDbH6rP98P1SVRsn1gHf_ovridEFbTyVr2w3TStwMHMA5zvNk-45HuL`
- **Auth**: OAuth 2.0 via clasp (george@upowerenergy.uk)

### Deploy Updates
```bash
cd /home/george/GB-Power-Market-JJ/revenue_comparison_clasp
cp ../Code.gs ./Code.gs
clasp push
```

### Manual Deployment (Alternative)
1. Open spreadsheet
2. Extensions → Apps Script
3. Copy `/home/george/GB-Power-Market-JJ/Code.gs`
4. Paste into editor
5. Save (Ctrl+S)
6. Refresh spreadsheet

---

## 📋 Current Sheets Structure

### BtM (Behind the Meter)
**Purpose**: Main battery site configuration

**Key Cells**:
- `A6`: Postcode (used by site marker function)
- `B6`: MPAN or Distributor ID (10-23)
- `C6`: DNO_Key (auto-populated)
- `D6`: DNO_Name (auto-populated)
- `B9`: Voltage Level (LV/HV)
- `B9-D9`: DUoS rates (Red/Amber/Green p/kWh)

**Menus**:
- `🔋 BESS Tools` → Refresh DNO Data
- `🗺️ DNO Map` → View Interactive Map / View Map with Site Markers

### DNO
**Purpose**: DNO reference data with center coordinates

**Columns**:
- A: DNO Region name
- B: Latitude (center point)
- C: Longitude (center point)
- D: MPAN ID
- E: Area (km²)
- F: Company name
- H: Embedded map (if using embed function)

---

## 🔄 DNO Lookup System

### Architecture
**Flow**: Button Click → Webhook → Python Script → BigQuery → Google Sheets

### Components

#### 1. Apps Script Button (`bess_auto_trigger.gs`)
```javascript
function manualRefreshDno() {
  var url = 'https://YOUR_NGROK_URL/refresh_dno';
  UrlFetchApp.fetch(url, {method: 'post'});
}
```

#### 2. Webhook Server (`dno_webhook_server.py`)
```python
# Flask on port 5001
@app.route('/refresh_dno', methods=['POST'])
def refresh_dno():
    subprocess.run(['python3', 'dno_lookup_python.py'])
    return jsonify({'status': 'success'})
```

#### 3. Lookup Script (`dno_lookup_python.py`)
- Reads postcode from `BtM!A6`
- Extracts MPAN core using `mpan_generator_validator`
- Queries BigQuery for DNO details
- Queries for DUoS rates by voltage level
- Updates cells `C6-H6` and `B9-D12`

### BigQuery Tables
- `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
- `inner-cinema-476211-u9.gb_power.duos_unit_rates`
- `inner-cinema-476211-u9.gb_power.duos_time_bands`

---

## 🎯 Roadmap

### Phase 1: Core Mapping ✅ COMPLETE
- [x] Real DNO boundaries visualization
- [x] Interactive Leaflet.js map
- [x] Postcode geocoding
- [x] Site marker plotting
- [x] Clasp deployment automation

### Phase 2: Enhanced Analytics (Planned)
- [ ] Multiple site markers (read from sheet range)
- [ ] Site comparison mode (side-by-side DNO costs)
- [ ] Historical DUoS rate charts
- [ ] Export map as PNG/PDF
- [ ] Custom color schemes (user-selectable)
- [ ] Distance calculator between sites

### Phase 3: Advanced Features (Future)
- [ ] Google Maps API integration (if API key available)
- [ ] Satellite imagery overlay
- [ ] Street view integration
- [ ] Driving directions between sites
- [ ] Heatmap of battery installations
- [ ] DNO capacity data overlay
- [ ] Grid connection queue visualization

### Phase 4: Automation (Future)
- [ ] Auto-refresh map on postcode change
- [ ] Scheduled DUoS rate updates
- [ ] Email alerts on rate changes
- [ ] Slack/Teams integration
- [ ] API endpoint for external systems

---

## 🐛 Known Issues

### Issue 1: GeoChart Incompatibility
**Problem**: Google GeoChart doesn't support UK DNO regions  
**Status**: ❌ Cannot fix (Google limitation)  
**Solution**: Using Leaflet.js instead (superior anyway)

### Issue 2: Embedded Map Interactivity
**Problem**: Google Sheets IMAGE() function doesn't support interactive HTML  
**Status**: ⚠️ Known limitation  
**Workaround**: Use modal map (menu option) for full interactivity

### Issue 3: Clasp OAuth Expiry
**Problem**: Clasp auth tokens expire periodically  
**Status**: ⚠️ Normal behavior  
**Solution**: Re-run `clasp login --no-localhost` when needed

### Issue 4: Large GeoJSON Load Time
**Problem**: 5.6MB GeoJSON takes 2-3 seconds to load  
**Status**: ✅ Acceptable (shows loading spinner)  
**Future**: Could implement caching or simplified boundaries

---

## 📚 Dependencies

### Python Packages
```bash
pip3 install --user \
  google-cloud-bigquery \
  gspread \
  oauth2client \
  flask \
  mpan-generator-validator
```

### Node.js Packages
```bash
npm install -g @google/clasp
```

### Google APIs Enabled
- Apps Script API
- Sheets API
- Drive API
- BigQuery API

---

## 🔐 Authentication

### Service Account
**File**: `/home/george/inner-cinema-credentials.json`  
**Project**: `inner-cinema-476211-u9`  
**Scopes**:
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/bigquery`

### Clasp OAuth
**Account**: `george@upowerenergy.uk`  
**Auth File**: `~/.clasprc.json`  
**Scopes**: Apps Script deployments, Drive access

---

## 📊 Performance Metrics

### Map Load Times
- GeoJSON fetch from GitHub: ~1-2 seconds
- Map render (14 regions): ~0.5 seconds
- Postcode geocoding: ~0.3 seconds
- Total modal open to interactive: ~2-3 seconds

### API Rate Limits
- **postcodes.io**: Unlimited (free tier)
- **BigQuery**: 1TB/month free queries
- **Google Sheets API**: 500 requests per 100 seconds

---

## 🧪 Testing

### Test Postcodes
```
SW1A 1AA  - Westminster (London, MPAN 11)
M1 1AE    - Manchester (North West, MPAN 22)
EH1 1YZ   - Edinburgh (Scotland, MPAN 21)
CF10 1EP  - Cardiff (South Wales, MPAN 19)
```

### Test Commands
```bash
# Test DNO lookup
python3 dno_lookup_python.py 14 HV

# Test webhook
curl -X POST http://localhost:5001/refresh_dno

# Test clasp deployment
cd revenue_comparison_clasp && clasp push --dry
```

---

## 📞 Support & Contacts

**Project Owner**: George Major  
**Email**: george@upowerenergy.uk  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

**Key Documentation**:
- `PROJECT_CONFIGURATION.md` - All config settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data pipeline details
- `.github/copilot-instructions.md` - AI assistant context

---

## 📝 Change Log

### v3.0 - 7 Dec 2025
- ✅ Added postcode geocoding with postcodes.io
- ✅ Implemented site marker plotting
- ✅ Created "View Map with Site Markers" menu
- ✅ Enhanced map with auto-zoom to sites
- ✅ Fixed clasp OAuth authentication

### v2.0 - 6 Dec 2025
- ✅ Added real DNO boundaries from GeoJSON
- ✅ Implemented Leaflet.js interactive maps
- ✅ Created 3 map viewing modes
- ✅ Set up clasp deployment pipeline

### v1.0 - 5 Dec 2025
- ✅ Initial DNO reference data in sheet
- ✅ Basic lat/lon center points
- ✅ Manual data entry workflow

---

## 💡 Ideas & Future Enhancements

### Map Enhancements
- Heat map layer showing battery density
- Time slider for historical DUoS rate changes
- Drawing tools for custom coverage areas
- Export map views as images
- Print-friendly map layouts

### Data Integrations
- Live grid frequency data overlay
- Substation location markers
- Constraint zones visualization
- Generation capacity by DNO
- Connection queue positions

### User Experience
- Dark mode for maps
- Mobile-responsive design
- Keyboard shortcuts for map navigation
- Bookmarkable map views
- Shareable map links

### Analytics
- Cost comparison calculator
- Optimal site location finder
- DNO selection wizard
- Revenue forecasting by region
- Multi-site portfolio optimizer

---

**End of Project Documentation**
