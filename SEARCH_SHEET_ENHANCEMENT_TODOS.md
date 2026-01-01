# Search Sheet Enhancement - Todo List
**Date**: December 31, 2025
**Status**: 🚧 PLANNING PHASE

---

## 📋 Todo List

### Phase 1: Google Sheets Search Interface (Priority 1)

#### 1. Create Search Sheet Layout ⏳ NOT STARTED
**Description**: Design professional search interface in Google Sheets with input fields and results table

**Tasks**:
- [ ] Create "Search" sheet if doesn't exist
- [ ] Add title header "🔍 ADVANCED PARTY & ASSET SEARCH"
- [ ] Create search criteria section (Rows 1-15)
- [ ] Create results section (Rows 17+)
- [ ] Add instructions/help section

**Layout**:
```
Row 1:  🔍 ADVANCED PARTY & ASSET SEARCH
Row 2:  [Blank]
Row 3:  📝 SEARCH CRITERIA
Row 4:  Date Range:                From: [DD/MM/YYYY B4] to [DD/MM/YYYY D4]
Row 5:  Party/Name Search:        [Input B5]
Row 6:  Record Type:               [Dropdown B6: None, All, BSC Party, BM Unit, NESO Project, TEC Project]
Row 7:  CUSC/BSC Role:            [Multi-select B7: None, All, VLP, VTP, Supplier, Embedded Power Station, ...]
Row 8:  Fuel/Technology Type:     [Multi-select B8: None, All, Battery, Wind, Solar, Gas, ...]
Row 9:  BM Unit ID:                [Dropdown B9: None, All, E_FARNB-1, E_HAWKB-1, ...]
Row 10: Organization:              [Dropdown B10: None, All, Drax Power Ltd, EDF Trading, ...]
Row 11: Capacity Range (MW):      [Min B11] to [Max D11]
Row 12: TEC Project Search:        [Input B12]
Row 13: Connection Site:           [Dropdown B13]
Row 14: Project Status:            [Dropdown B14: None, All, Active, Complete, Withdrawn, ...]
Row 15: [Blank]
Row 16: [🔍 Search Button]  [🧹 Clear Button]  [ℹ️ Help Button]
Row 17: [Blank]
Row 18: 📊 SEARCH RESULTS          [Last Search: timestamp]  [Results: count]
Row 19: [Blank]
Row 20: [Table Headers - 11 columns]
Row 21+: [Results Data]
```

---

#### 2. Populate Search Dropdowns ⏳ NOT STARTED
**Description**: Create fully populated dropdowns with "None" and "All" at top, rest alphabetically sorted

**Dropdowns Required**:

**B4 - Date Range** (NEW):
```
From Date: [DD/MM/YYYY picker]
To Date:   [DD/MM/YYYY picker]
```

**B6 - Record Type**:
```
None
All
BSC Party
BM Unit
NESO Project
TEC Project (Connection Queue)
Generator
Supplier
Interconnector
```

**B7 - CUSC/BSC Role** (Multi-select via data validation):
```
None
All
---
Distribution System (DNO/IDNO)
Embedded Exemptable Large Power Station
Embedded Power Station
Large Power Station
Non-Embedded Customer (Demand)
Small Power Station Trading Party
Supplier
Virtual Lead Party (VLP)
Virtual Trading Party (VTP)
```

**B8 - Fuel/Technology Type** (Multi-select):
```
None
All
---
Battery Storage
Biomass
CCGT (Gas)
Coal
Demand Side Response
Hydro
Interconnector
Nuclear
OCGT (Gas)
Offshore Wind
Onshore Wind
Pumped Storage
Solar
Wave/Tidal
```

**B9 - BM Unit ID** (Query from BigQuery):
```
None
All
---
[200+ BMU IDs alphabetically sorted]
E_CARR-2
E_FARNB-1
E_HAWKB-1
...
```

**B10 - Organization** (Query from BigQuery):
```
None
All
---
[Party/company names alphabetically sorted]
Centrica Energy Trading
Drax Power Limited
EDF Trading Ltd
Scottish Power
SSE Generation Ltd
...
```
```
None
All
---
Battery
Biomass
Coal
Gas (CCGT)
Gas (OCGT)
Hydro
Interconnector
Nuclear
Oil
Pumped Storage
Solar
Wave/Tidal
Wind (Offshore)
Wind (Onshore)
```

**B13 - Connection Site** (From TEC data):
```
None
All
---
[Sites alphabetically sorted]
```

**B14 - Project Status**:
```
None
All
---
Accepted
Active
Completed
Connection Offer Made
Contracted
Energised
Modification Accepted
Scoping Ongoing
Withdrawn
```

---

#### 3. Create Results Table (Columns) ⏳ NOT STARTED
**Description**: Design 11-column results table matching search output format (Role and Organization separated)

**Table Schema**:
| Column | Header | Description | Example |
|--------|--------|-------------|---------|
| A | Record Type | Type of entity | BSC Party, BM Unit, TEC Project |
| B | Identifier (ID) | Unique ID/code | P1234, E_FARNB-1, a0l4L0000005iPb |
| C | Name | Display name | EDF Trading Ltd, Farnborough BESS |
| D | Role | CUSC/BSC category | Virtual Trading Party, Supplier, VLP |
| E | Organization | Owning company | Drax Power Limited, EDF Energy |
| F | Extra Info | Additional details | Qualified Person, Connection site |
| G | Capacity (MW) | Generator capacity | 50, 660, 1200 |
| H | Fuel Type | Energy source | Battery, Wind, Gas |
| I | Status | Current state | Active, Energised, Withdrawn |
| J | Dataset Source | Origin | ELEXON, BMRS, NESO, TEC |
| K | Match Score | Relevance | 85, 92, 100 |

**Formatting**:
- Header row: Bold, centered, gray background (#E0E0E0)
- Data rows: Alternating white/light blue (#F0F8FF)
- Frozen rows: 1-19 (search criteria visible while scrolling)
- Column widths: Auto-fit with minimum 80px

---

#### 4. Add TEC (Connection Queue) Search ⏳ NOT STARTED
**Description**: Integrate NESO Transmission Entry Capacity (TEC) connection queue data

**TEC Data Fields**:
- Project Name (e.g., "Lower 48 Energy BESS")
- Customer Name (party)
- Connection Site
- MW Capacity
- Technology Type
- Stage/Status
- Project ID (e.g., a0l4L0000005iPb)
- Connection Date
- DNO/TO (Distribution/Transmission Operator)

**Implementation**:
```python
class TECFetcher:
    def fetch_tec_projects(self, term: str) -> pd.DataFrame:
        """Fetch from NESO TEC register"""
        # NESO TEC dataset ID
        # Search by project name, customer, connection site
        # Return matching projects
```

**Query Example**:
```python
# Search TEC by project name
results = search_tec(project_name="Lower 48")
# Returns: Lower 48 Energy BESS, 50 MW, Battery, Connection Offer Made
```

---

#### 5. Create Party Details Panel ⏳ NOT STARTED
**Description**: Display detailed information when party is selected from results

**Panel Location**: Columns L-P, Rows 5-25

**Panel Layout**:
```
Row 5:  📋 PARTY DETAILS
Row 6:  [Blank]
Row 7:  Selected: [Party Name from clicked row]
Row 8:  [Blank]
Row 9:  Party ID:           [Value]
Row 10: Record Type:        [Value]
Row 11: Categories:         [Value]
Row 12: [Blank]
Row 13: 📊 ROLES & QUALIFICATIONS
Row 14: BSC Roles:          [List of roles]
Row 15: VLP Status:         [Yes/No + details]
Row 16: VTP Status:         [Yes/No + details]
Row 17: Qualification:      [Status]
Row 18: [Blank]
Row 19: 🏭 ASSETS OWNED
Row 20: BM Units:           [Count]
Row 21: Total Capacity:     [MW]
Row 22: Fuel Types:         [List]
Row 23: [Blank]
Row 24: 📅 LAST UPDATED
Row 25: Date:               [Timestamp]
```

**Data Sources**:
- `dim_party` table (BigQuery)
- `bmu_registration_data` table (BigQuery)
- `Party_Wide` tab (current sheet)
- Elexon BSC Signatories

---

### Phase 2: Apps Script Integration (Priority 2)

#### 6. Create Search Button Handler ⏳ NOT STARTED
**Description**: Apps Script function to trigger Python search when button clicked

**File**: `search_interface.gs`

**Functions**:
```javascript
function onSearchButtonClick() {
    // Read search criteria from B5-B13
    // Call webhook server or show manual command
    // Display progress message
}

function onClearButtonClick() {
    // Clear all input fields
    // Clear results table
}

function onHelpButtonClick() {
    // Show search instructions dialog
}

function onRowClick(row) {
    // Detect clicked result row
    // Extract party/entity details
    // Populate Party Details panel (L5-P25)
}
```

---

#### 7. Enable Multi-Select Dropdowns ⏳ NOT STARTED
**Description**: Allow selecting multiple categories, fuel types, etc.

**Implementation Options**:

**Option A: Comma-Separated (Simple)**
```javascript
// Data validation allows manual entry
// User types: "VLP, Generator, Battery Storage"
// Apps Script splits on comma
```

**Option B: Checkbox Dialog (Advanced)**
```javascript
function showCategoryPicker() {
    var html = HtmlService.createHtmlOutput(`
        <form>
            <input type="checkbox" name="cat" value="VLP"> VLP
            <input type="checkbox" name="cat" value="Generator"> Generator
            ...
            <button onclick="applySelection()">Apply</button>
        </form>
    `);
    SpreadsheetApp.getUi().showModalDialog(html, 'Select Categories');
}
```

**Recommended**: Option A for Phase 1, Option B for Phase 2+

---

#### 8. Create Alphabetical Sorting for Dropdowns ⏳ NOT STARTED
**Description**: Ensure "None", "All" at top, rest alphabetically sorted

**Implementation**:
```python
def format_dropdown_options(items: List[str]) -> List[str]:
    """Format dropdown with None, All at top, rest sorted"""
    # Remove None/All from items if present
    filtered = [x for x in items if x not in ["None", "All"]]

    # Sort alphabetically (case-insensitive)
    sorted_items = sorted(filtered, key=lambda x: x.lower())

    # Add None and All at top
    return ["None", "All"] + sorted_items

# Example usage
categories = ["Generator", "VLP", "Supplier", "Wind", "Battery"]
dropdown_options = format_dropdown_options(categories)
# Result: ["None", "All", "Battery", "Generator", "Supplier", "VLP", "Wind"]
```

---

### Phase 3: Python Backend Enhancements (Priority 3)

#### 9. Add TEC Search to Python Script ⏳ NOT STARTED
**Description**: Extend `advanced_search_tool_enhanced.py` with TEC data source

**New Class**:
```python
class TECFetcher:
    """Fetch NESO TEC connection queue data"""

    def __init__(self, cache: CacheManager):
        self.cache = cache
        self.neso_base = "https://api.neso.energy"

    def fetch_tec_projects(self, filters: Dict) -> pd.DataFrame:
        """
        Search TEC register

        Args:
            filters: {
                'project_name': str,
                'customer_name': str,
                'connection_site': str,
                'capacity_min': int,
                'capacity_max': int,
                'status': str,
                'technology': str
            }
        """
        # Fetch from NESO TEC API/dataset
        # Apply filters
        # Return DataFrame
```

**Integration**:
```python
class SearchEngine:
    def search(self, ...):
        # Add TEC search
        if filters.get('tec_search'):
            tec_results = self.tec.fetch_tec_projects(filters)
            all_results.extend(self._format_tec_results(tec_results))
```

---

#### 10. Read Multi-Select Values from Sheet ⏳ NOT STARTED
**Description**: Parse comma-separated or multi-line selections

**Implementation**:
```python
def parse_multiselect(value: str) -> List[str]:
    """Parse multi-select dropdown value"""
    if not value or value.strip().lower() in ['none', '']:
        return []

    if value.strip().lower() == 'all':
        return ['All']

    # Split by comma, newline, or semicolon
    items = []
    for sep in [',', '\n', ';']:
        if sep in value:
            items = [x.strip() for x in value.split(sep)]
            break
    else:
        items = [value.strip()]

    return [x for x in items if x]

# Example usage
categories_input = "VLP, Generator, Battery Storage"
categories = parse_multiselect(categories_input)
# Result: ["VLP", "Generator", "Battery Storage"]
```

---

#### 11. Add Capacity Range Filter ⏳ NOT STARTED
**Description**: Filter results by MW capacity range

**Implementation**:
```python
def filter_by_capacity(
    results: List[SearchResult],
    min_mw: Optional[float] = None,
    max_mw: Optional[float] = None
) -> List[SearchResult]:
    """Filter results by capacity range"""
    filtered = []

    for r in results:
        if not r.capacity_mw:
            continue

        try:
            capacity = float(r.capacity_mw)

            if min_mw is not None and capacity < min_mw:
                continue

            if max_mw is not None and capacity > max_mw:
                continue

            filtered.append(r)
        except (ValueError, TypeError):
            # Keep results without valid capacity
            filtered.append(r)

    return filtered
```

---

#### 12. Implement Party Details Lookup ⏳ NOT STARTED
**Description**: When row clicked, fetch full party details

**Implementation**:
```python
class PartyDetailsProvider:
    """Fetch comprehensive party information"""

    def get_party_details(self, party_id: str, party_name: str) -> Dict:
        """Fetch all details for a party"""
        details = {
            'basic_info': self._get_basic_info(party_id, party_name),
            'bsc_roles': self._get_bsc_roles(party_name),
            'vlp_vtp_status': self._get_vlp_vtp_status(party_id),
            'assets': self._get_owned_assets(party_name),
            'capacity_summary': self._get_capacity_summary(party_name),
            'recent_activity': self._get_recent_activity(party_id)
        }
        return details

    def _get_owned_assets(self, party_name: str) -> List[Dict]:
        """Query BigQuery for BMUs owned by party"""
        query = f"""
        SELECT elexonbmunit, fueltype, registeredcapacity
        FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
        WHERE leadpartyname = '{party_name}'
        ORDER BY registeredcapacity DESC
        """
        # Execute and return results
```

---

### Phase 4: Advanced Features (Priority 4)

#### 13. Add Export Options ⏳ NOT STARTED
**Description**: Export search results to CSV, JSON, or BigQuery table

**Options**:
- **CSV**: Download to local file
- **JSON**: API-compatible format
- **BigQuery**: Write to `search_results` table for analysis

---

#### 14. Create Search History ⏳ NOT STARTED
**Description**: Track recent searches for quick re-run

**Implementation**:
- Store last 10 searches in sheet tab "Search History"
- Click to reload criteria
- Track most-used filters

---

#### 15. Add Fuzzy Match Confidence ⏳ NOT STARTED
**Description**: Show match quality in results

**Display**:
- 90-100: Exact match (green)
- 70-89: Good match (yellow)
- 50-69: Possible match (orange)
- <50: Weak match (red/hidden)

---

#### 16. Implement Saved Searches ⏳ NOT STARTED
**Description**: Save common search configurations

**Features**:
- Name and save search criteria
- Quick-load from dropdown
- Share search configs between users

---

#### 17. Add Batch Search ⏳ NOT STARTED
**Description**: Search multiple parties at once

**Example**:
```
Input: "Drax, SSE, EDF, Flexgen"
Output: Results for all 4 parties combined
```

---

#### 18. Add Date Range Filter with Date Pickers ⏳ NOT STARTED
**Description**: Enable date range filtering with DD/MM/YYYY format dropdowns

**Implementation**:
```python
def add_date_pickers(sheet):
    """Add date picker data validation"""
    # Create date validation for B4 and D4
    # Format: DD/MM/YYYY
    # Range: 2020-01-01 to today + 2 years

def parse_date_range(from_date: str, to_date: str) -> Tuple[date, date]:
    """Parse DD/MM/YYYY strings to date objects"""
    # Handle formats: "01/01/2025", "1/1/25"
    # Return (start_date, end_date)
```

**Sheet Integration**:
```
Row 4:  Date Range: [From: 01/01/2025] to [To: 31/12/2025]
```

**Apps Script Calendar Picker**:
```javascript
function showDatePicker(cell) {
    var html = HtmlService.createHtmlOutput(`
        <input type="date" id="datePicker">
        <button onclick="applyDate()">OK</button>
    `);
    SpreadsheetApp.getUi().showModalDialog(html, 'Select Date');
}
```

---

#### 19. Separate Role and Organization Columns ⏳ NOT STARTED
**Description**: Split combined "Role/Organization" into two distinct columns

**CUSC/BSC Role Categories** (Column D):
Based on CUSC Section 1 definitions:
```python
CUSC_ROLES = [
    "Power Station (Directly Connected)",      # Large generators at transmission
    "Large Power Station",                      # Alternative term
    "Non-Embedded Customer",                    # Demand at transmission level
    "Distribution System",                      # DNO/IDNO connected at transmission
    "Supplier",                                 # Entities purchasing transmission use
    "Embedded Power Station",                   # Generation at distribution level
    "Embedded Exemptable Large Power Station",  # Specific embedded type
    "Small Power Station Trading Party",        # Small generation parties
    "Virtual Lead Party (VLP)",                 # Aggregators under VLP regime
    "Virtual Trading Party (VTP)",              # Virtual trading entities
    "Interconnector User",                      # Cross-border connections
]
```

**Organization Categories** (Column E):
Actual company/entity names:
```python
def fetch_organizations() -> List[str]:
    """Query BigQuery for unique party/company names"""
    query = f"""
    SELECT DISTINCT leadpartyname as organization
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE leadpartyname IS NOT NULL
    UNION DISTINCT
    SELECT DISTINCT partyname as organization
    FROM `{PROJECT_ID}.{DATASET}.dim_party`
    WHERE partyname IS NOT NULL
    ORDER BY organization
    """
    # Returns: Drax Power Limited, EDF Trading Ltd, SSE, etc.
```

**Data Mapping**:
```python
@dataclass
class SearchResult:
    type: str          # BSC Party, BM Unit, TEC Project
    id: str            # P1234, E_FARNB-1
    name: str          # Display name
    role: str          # CUSC/BSC role (NEW - separated)
    organization: str  # Company name (NEW - separated)
    extra: str         # Additional info
    capacity_mw: float
    fuel_type: str
    status: str
    source: str
    score: int
```

**Example Results**:
| Type | ID | Name | Role | Organization | Extra |
|------|----|----|------|--------------|-------|
| BSC Party | P1234 | EDF Trading Ltd | Supplier | EDF Energy | Qualified Person |
| BM Unit | E_FARNB-1 | Farnborough BESS | Virtual Lead Party (VLP) | Flexgen Power Systems | 50 MW Battery |
| TEC Project | a0l4L0000005iPb | Lower 48 BESS | Embedded Power Station | Lower 48 Energy Ltd | Connection Offer Made |

**Data Source Integration**:
```python
class RoleOrganizationMapper:
    """Map entities to CUSC roles and organizations"""

    def get_cusc_role(self, party_type: str, capacity_mw: float) -> str:
        """Determine CUSC role based on connection type and capacity"""
        # Logic based on CUSC Section 1 definitions

    def get_organization(self, party_id: str, bmu_id: str) -> str:
        """Fetch owning organization from BigQuery"""
        # Query dim_party or bmu_registration_data
```

---

#### 20. Create Search Analytics ⏳ NOT STARTED
**Description**: Track search patterns and popular queries

**Metrics**:
- Most searched parties
- Common category combinations
- Search success rate
- Average result count

---

## 🎯 Implementation Priority

### Week 1 (Jan 1-7, 2026)
- ✅ Todo #1: Create Search Sheet Layout
- ✅ Todo #2: Populate Search Dropdowns
- ✅ Todo #3: Create Results Table (11 columns)
- ✅ Todo #8: Alphabetical Sorting
- ✅ Todo #18: Add Date Range Filter
- ✅ Todo #19: Separate Role and Organization

### Week 2 (Jan 8-14, 2026)
- ✅ Todo #4: Add TEC Search
- ✅ Todo #9: TEC Python Backend
- ✅ Todo #10: Multi-Select Parsing
- ✅ Todo #11: Capacity Range Filter

### Week 3 (Jan 15-21, 2026)
- ✅ Todo #5: Party Details Panel
- ✅ Todo #6: Search Button Handler
- ✅ Todo #12: Party Details Lookup

### Week 4 (Jan 22-28, 2026)
- ✅ Todo #7: Multi-Select Dropdowns
- ✅ Todo #13-17, #20: Advanced Features (as time permits)

---

## 📊 Success Criteria

### Must Have (Phase 1)
- ✅ Search sheet with all input fields
- ✅ Date range filter (DD/MM/YYYY format)
- ✅ Dropdowns populated with "None", "All", sorted options
- ✅ Multi-select via comma-separated values
- ✅ Results table with 11 columns (Role and Organization separated)
- ✅ CUSC/BSC role categorization
- ✅ TEC project search integration
- ✅ Party details panel

### Should Have (Phase 2-3)
- ✅ Apps Script buttons working
- ✅ Click-to-view party details
- ✅ Capacity range filtering
- ✅ Multi-source search (ELEXON + BMRS + NESO + TEC + BigQuery)

### Nice to Have (Phase 4)
- ⏳ Export to CSV/JSON
- ⏳ Search history
- ⏳ Saved searches
- ⏳ Batch search
- ⏳ Analytics dashboard

---

## 🔗 Related Files

**Python Scripts**:
- `advanced_search_tool_enhanced.py` - Main search engine
- `create_search_interface.py` - Sheet layout creator (to be created)
- `tec_fetcher.py` - TEC data integration (to be created)

**Apps Script**:
- `search_interface.gs` - Button handlers (to be created)
- `party_details_panel.gs` - Details lookup (to be created)

**Documentation**:
- `ADVANCED_SEARCH_IMPROVEMENTS.md` - Technical docs
- `SEARCH_SHEET_USER_GUIDE.md` - User manual (to be created)

---

## 📝 Notes

**TEC Data Source**:
- NESO Transmission Entry Capacity Register
- Updated monthly
- Contains connection queue: accepted, contracted, energised, withdrawn projects
- Key for future pipeline analysis

**Multi-Select Limitations**:
- Google Sheets native dropdowns don't support multi-select checkboxes
- Workaround: Comma-separated values + Apps Script custom dialog

**Performance**:
- Cache all dropdown data (24h TTL)
- Lazy-load party details (on-demand)
- Paginate results if >100 rows

---

*Last Updated: December 31, 2025*
*Next Review: After Phase 1 completion*
