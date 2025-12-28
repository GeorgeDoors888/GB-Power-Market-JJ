# Google Sheets Advanced Visualization Guide

## 📊 Sparklines (Mini Charts in Cells)

### Types Available:
1. **LINE** - Trending data over time
2. **COLUMN** - Bar chart in a cell
3. **WINLOSS** - Above/below baseline
4. **AREA** - Filled line chart

### Sparkline Examples:

```javascript
// Basic line sparkline
=SPARKLINE(B2:B50)

// Column chart with colors
=SPARKLINE(Data_Hidden!B29:BI29, {"charttype","column"; "color","#0066cc"; "negcolor","red"})

// Win/Loss (shows +/- changes)
=SPARKLINE(B2:B50, {"charttype","winloss"; "color","green"; "negcolor","red"})

// Area chart with axis
=SPARKLINE(B2:B50, {"charttype","area"; "color","#4285f4"; "linewidth",2; "rtl",true})

// Multiple options
=SPARKLINE(Data_Hidden!B29:BI29, {
  "charttype", "column";
  "color", "#34A853";
  "negcolor", "#EA4335";
  "axis", true;
  "axiscolor", "#666666";
  "ymin", 0;
  "ymax", 100
})
```

### Sparkline Options:
- `charttype`: "line", "column", "winloss", "area"
- `color`: Hex color or named color
- `negcolor`: Color for negative values
- `linewidth`: 1-10 pixels
- `axis`: true/false (show zero line)
- `axiscolor`: Axis line color
- `ymin`, `ymax`: Set Y-axis range
- `rtl`: Right-to-left (reverse data order)
- `nan`: "ignore" or "convert" (handle missing data)

## 📈 Advanced Chart Types in Google Sheets

### 1. Combo Charts (Line + Column)
Perfect for comparing trends with absolute values
```
Insert → Chart → Combo chart
- Series 1: Column (e.g., Volume)
- Series 2: Line (e.g., Price)
- Dual Y-axis for different scales
```

### 2. Candlestick Charts
For financial/price data (Open, High, Low, Close)
```
Insert → Chart → Candlestick chart
Requires 4 columns: Open, High, Low, Close
```

### 3. Waterfall Charts
Show cumulative effect of sequential values
```
Insert → Chart → Waterfall chart
Great for: Revenue breakdown, cost analysis
```

### 4. Gauge Charts
Speedometer-style visualizations
```
Insert → Chart → Gauge chart
Shows single value against min/max
```

### 5. Geo Charts (Maps!)
Built-in mapping without Google Maps API
```
Insert → Chart → Geo chart
- Can show countries, regions, cities
- Color-coded by value
- UK regions: GB-ENG, GB-SCT, GB-WLS, GB-NIR
```

### 6. Treemap Charts
Hierarchical data visualization
```
Insert → Chart → Treemap
Shows nested categories with size = value
```

### 7. Histogram
Distribution analysis
```
Insert → Chart → Histogram
Automatic binning of continuous data
```

### 8. Scatter Charts with Trendlines
Statistical analysis
```
Insert → Chart → Scatter chart
Add trendline: Linear, Exponential, Polynomial
Show R² value for correlation
```

## 🗺️ Maps in Google Sheets

### Option 1: Built-in Geo Charts (No API needed!)

**Example for UK Power Regions:**
```javascript
// In Apps Script (Code.gs)
function createUKPowerMap() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var dataRange = sheet.getRange("A1:C15"); // Region, Value, Label
  
  var chart = sheet.newChart()
    .asGeoChart()
    .addRange(dataRange)
    .setOption('region', 'GB')  // Focus on Great Britain
    .setOption('resolution', 'provinces')
    .setOption('colorAxis', {
      colors: ['#e7f0fa', '#4285f4', '#1a0dab'],
      minValue: 0,
      maxValue: 100
    })
    .setOption('backgroundColor', '#f0f0f0')
    .setOption('datalessRegionColor', '#e0e0e0')
    .setPosition(5, 5, 0, 0)
    .build();
  
  sheet.insertChart(chart);
}
```

**UK DNO Regions Data Format:**
```
Region Code | Region Name           | Value
GB-ENG      | England              | 1500
GB-SCT      | Scotland             | 300
GB-WLS      | Wales                | 200
```

**For DNO Territories (more granular):**
You'll need to use Custom Maps with lat/long coordinates.

### Option 2: Google Maps Integration (Requires API Key)

**A. Simple Location Markers:**
```javascript
// Apps Script function
function showMapDialog() {
  var html = HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY"></script>
      </head>
      <body>
        <div id="map" style="width: 100%; height: 500px;"></div>
        <script>
          function initMap() {
            var map = new google.maps.Map(document.getElementById('map'), {
              center: {lat: 54.5, lng: -3.5}, // Center UK
              zoom: 6
            });
            
            // Add generator markers
            var generators = [
              {lat: 53.0, lng: -1.5, name: "Drax Power Station"},
              {lat: 51.5, lng: -0.1, name: "London Interconnector"}
            ];
            
            generators.forEach(function(gen) {
              new google.maps.Marker({
                position: {lat: gen.lat, lng: gen.lng},
                map: map,
                title: gen.name
              });
            });
          }
          initMap();
        </script>
      </body>
    </html>
  `).setWidth(800).setHeight(600);
  
  SpreadsheetApp.getUi().showModalDialog(html, 'UK Power Generators Map');
}
```

**B. Heat Maps (Intensity):**
```javascript
// Show power generation intensity
var heatmapData = [
  {location: new google.maps.LatLng(53.0, -1.5), weight: 3960}, // Drax
  {location: new google.maps.LatLng(52.8, -1.3), weight: 2000}  // Ratcliffe
];

var heatmap = new google.maps.visualization.HeatmapLayer({
  data: heatmapData,
  radius: 30,
  gradient: [
    'rgba(0, 255, 255, 0)',
    'rgba(0, 255, 255, 1)',
    'rgba(0, 191, 255, 1)',
    'rgba(0, 127, 255, 1)',
    'rgba(255, 0, 0, 1)'
  ]
});
heatmap.setMap(map);
```

### Option 3: Custom SVG Maps (Best for DNO Territories)

**Create custom UK DNO boundary map:**
```html
<!-- In HTML sidebar (APPS_SCRIPT_DNOMAP.html) -->
<svg viewBox="0 0 500 700" id="uk-dno-map">
  <!-- NGED West Midlands -->
  <path d="M 200,300 L 250,280 L 270,320 L 230,340 Z" 
        fill="#4285f4" 
        data-dno="NGED-WMID"
        data-rate="1.764"
        class="dno-region"/>
  
  <!-- NPG North East -->
  <path d="M 280,100 L 320,80 L 340,140 L 300,160 Z"
        fill="#34a853"
        data-dno="NPG-NEAST"
        data-rate="2.134"
        class="dno-region"/>
        
  <!-- Add all 14 DNO regions -->
</svg>

<script>
document.querySelectorAll('.dno-region').forEach(function(region) {
  region.addEventListener('click', function() {
    var dno = this.dataset.dno;
    var rate = this.dataset.rate;
    alert(dno + ': ' + rate + ' p/kWh');
  });
  
  region.addEventListener('mouseover', function() {
    this.style.opacity = '0.7';
  });
  
  region.addEventListener('mouseout', function() {
    this.style.opacity = '1';
  });
});
</script>
```

## 🎨 Your Current Project: GB Live Dashboard

### Active Sparklines:
```javascript
// Row 14 - MID Price (Working ✅)
=SPARKLINE(Data_Hidden!B29:BI29, {"charttype","column"; "color","#0066cc"})

// Row 16 - System Buy Price (Working ✅)
=SPARKLINE(Data_Hidden!B30:BI30, {"charttype","column"; "color","#ea4335"})

// Row 18 - BM-MID Spread (Working ✅)
=SPARKLINE(Data_Hidden!B32:BI32, {"charttype","column"; "color","orange"; "negcolor","green"})
```

### Recommended Advanced Charts for Your Data:

**1. Combo Chart - Price vs Volume**
- X-axis: Settlement Period
- Y1-axis (Columns): MWh Volume
- Y2-axis (Line): £/MWh Price
- Shows price-volume relationship

**2. Geo Chart - DNO Rate Map**
- Region: GB (Great Britain)
- Color scale: DUoS rates (p/kWh)
- Tooltip: DNO name + rates

**3. Treemap - BM Unit Revenue**
- Size = Revenue (£)
- Color = Unit type (Gas, Wind, Battery)
- Labels = BM Unit ID

**4. Waterfall - Daily Revenue Breakdown**
- Start: Day-ahead forecast
- +/- BM acceptances
- +/- Imbalance charges
- End: Total daily revenue

## 🔧 Implementation Guide

### Quick Setup for Maps:

**Option A: No API Key (Built-in Geo Chart)**
```javascript
// In GB Live sheet
function addDNOMap() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('GB Live');
  
  // Create data for chart
  var data = [
    ['Region', 'DUoS Rate (p/kWh)'],
    ['GB-ENG-WMID', 1.764],  // NGED West Midlands
    ['GB-ENG-SWLS', 1.891],  // NGED South Wales
    ['GB-SCT', 2.134]        // SSEN North
  ];
  
  var dataRange = sheet.getRange(40, 1, data.length, 2);
  dataRange.setValues(data);
  
  var chart = sheet.newChart()
    .asGeoChart()
    .addRange(dataRange)
    .setOption('region', 'GB')
    .setPosition(40, 4, 0, 0)
    .build();
    
  sheet.insertChart(chart);
}
```

**Option B: With API Key (Full Google Maps)**
1. Get API key: https://console.cloud.google.com/apis/credentials
2. Enable Maps JavaScript API
3. Add to Apps Script HTML sidebar
4. Use custom markers/heatmaps

### Your Next Steps:

1. **Add More Sparklines** - You have 34 settlement periods → can show trends
2. **Create Combo Charts** - Price + Volume analysis
3. **Add DNO Geo Chart** - Visual UK map with DUoS rates
4. **Implement Interactive Map** - Click DNO region → show details

Want me to implement any of these for your dashboard?
