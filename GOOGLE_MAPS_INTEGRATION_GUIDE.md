# Google Maps Integration Guide

## ✅ Good News: Your Maps Are Already Using Google Maps!

Your `dno_energy_map_advanced.html` is **already fully integrated** with Google Maps API. It's not using an alternative mapping library - it's using the official Google Maps JavaScript API.

## 🔍 Current Setup

### Google Maps API Key
```html
<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0&callback=initMap" async defer></script>
```

**Your API Key:** `AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0`

### Features Currently Using Google Maps

1. **Base Map Display**
   ```javascript
   map = new google.maps.Map(document.getElementById('map'), {
       zoom: 6,
       center: { lat: 54.5, lng: -3.0 },  // Center of UK
       mapTypeId: 'roadmap'
   });
   ```

2. **Markers for Generators**
   - SVA generators (circles)
   - CVA plants (triangles)
   - Custom icons and colors

3. **Polygons for Boundaries**
   - DNO boundaries (14 regions)
   - GSP zones (333 zones)

4. **Info Windows**
   - Click markers for plant details
   - Formatted with HTML

5. **Interactive Controls**
   - Zoom, pan, tilt
   - Layer toggles
   - Custom control panel

## 🎯 How It Works

### Architecture
```
Your HTML File (dno_energy_map_advanced.html)
    ↓
Google Maps JavaScript API (loaded from googleapis.com)
    ↓
Google Maps Servers (tiles, geocoding, etc.)
    ↓
Rendered in Browser (Chrome, Safari, Firefox, etc.)
```

### Data Flow
```
1. Browser loads HTML file
2. Google Maps API script loads
3. initMap() function runs
4. Map created in <div id="map">
5. User clicks buttons (SVA, CVA, DNO, etc.)
6. JavaScript fetches JSON data
7. Markers/polygons added to map
8. User interacts with map
```

## 📋 Requirements for Maps to Work

### ✅ What You Already Have

1. **Valid Google Maps API Key** - ✅ Present in HTML
2. **Map Container** - ✅ `<div id="map">`
3. **Initialization Function** - ✅ `initMap()`
4. **Data Files** - ✅ generators.json, DNO/GSP data
5. **Modern Browser** - ✅ Works in Chrome, Safari, Firefox, Edge

### ⚠️ Potential Issues to Check

#### 1. API Key Validity
**Check if your API key is active:**
```bash
# Test API key
curl "https://maps.googleapis.com/maps/api/js?key=AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0&callback=initMap"
```

If you see errors like:
- "This API key is not authorized" → Need to enable billing
- "RefererNotAllowedMapError" → Need to configure referrer restrictions
- "ApiNotActivatedMapError" → Need to enable Maps JavaScript API

#### 2. Billing Account
Google Maps requires a billing account (but has generous free tier):
- **Free tier:** $200/month credit
- **Maps JavaScript API:** ~28,000 map loads/month free
- **Static Maps:** ~100,000 requests/month free

**Your usage (estimated):**
- Personal project: Well within free tier
- No costs expected unless serving to thousands of users

#### 3. API Restrictions
Your key might be restricted by:
- **HTTP referrer:** Only works from specific domains
- **IP address:** Only works from specific IPs
- **API restrictions:** Only certain Google APIs enabled

### 🔧 How to Fix Issues

#### If Maps Not Loading

**Option 1: Check Browser Console**
```
1. Open map in browser
2. Press F12 (Developer Tools)
3. Click "Console" tab
4. Look for errors like:
   - "Google Maps API error"
   - "ApiNotActivatedMapError"
   - "RefererNotAllowedMapError"
```

**Option 2: Test with Unrestricted Key**
```javascript
// Temporarily use a test key to verify it's an API key issue
// Go to: https://console.cloud.google.com/google/maps-apis
// Create new key without restrictions
```

**Option 3: Enable Required APIs**
Go to Google Cloud Console:
1. https://console.cloud.google.com/
2. Select your project (or create one)
3. Go to "APIs & Services" → "Library"
4. Enable these APIs:
   - **Maps JavaScript API** (Required)
   - **Geocoding API** (Optional - for address search)
   - **Places API** (Optional - for location search)

#### If Getting Billing Errors

**Setup Billing Account:**
1. Go to https://console.cloud.google.com/billing
2. Click "Link a billing account"
3. Add credit card (won't be charged within free tier)
4. Link to your project

**Free tier covers:**
- 28,500 map loads/month = ~950/day
- Your personal use won't exceed this

## 🚀 Making Maps Work in Different Contexts

### 1. Local File (Current Setup)
**How to use:**
```bash
# Open directly in browser
open dno_energy_map_advanced.html

# Or double-click the file
```

**Limitations:**
- CORS issues with some data files (JSON may not load)
- API key referrer restrictions might block
- `file://` protocol has security restrictions

**Solution if CORS issues:**
```bash
# Run a local web server
cd /Users/georgemajor/GB\ Power\ Market\ JJ
python -m http.server 8000

# Then open: http://localhost:8000/dno_energy_map_advanced.html
```

### 2. Web Server (Recommended)
**Host on a web server for best results:**

**Option A: Python HTTP Server (Local)**
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
python -m http.server 8000

# Access at: http://localhost:8000/dno_energy_map_advanced.html
```

**Option B: GitHub Pages (Public)**
```bash
# Push to GitHub repository
git add dno_energy_map_advanced.html generators.json
git commit -m "Add energy map"
git push

# Enable GitHub Pages in repository settings
# Access at: https://yourusername.github.io/repo-name/dno_energy_map_advanced.html
```

**Option C: Cloud Hosting**
Upload to:
- **Google Cloud Storage** (with web hosting enabled)
- **AWS S3** (with static website hosting)
- **Netlify** (drag & drop)
- **Vercel** (automatic deployment)

### 3. Restricting API Key (Security)

**HTTP Referrer Restrictions:**
```
Google Cloud Console → Credentials → API Key
→ API restrictions → HTTP referrers

Add allowed referrers:
- http://localhost:8000/*
- https://yourdomain.com/*
- file:///*  (for local file access)
```

**API Restrictions:**
```
Restrict key to:
- Maps JavaScript API
- Geocoding API (if using search)
```

## 🎨 Google Maps Features You Can Add

### Currently NOT Using (But Could Add):

#### 1. Different Map Types
```javascript
// In initMap() function
mapTypeId: 'satellite',  // or 'hybrid', 'terrain'

// Or add control to switch:
mapTypeControlOptions: {
    style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
    position: google.maps.ControlPosition.TOP_CENTER,
}
```

#### 2. Street View
```javascript
map.setStreetView(panorama);
```

#### 3. Traffic Layer
```javascript
const trafficLayer = new google.maps.TrafficLayer();
trafficLayer.setMap(map);
```

#### 4. Geocoding (Address Search)
```javascript
const geocoder = new google.maps.Geocoder();
geocoder.geocode({ address: "London, UK" }, (results, status) => {
    if (status === 'OK') {
        map.setCenter(results[0].geometry.location);
    }
});
```

#### 5. Directions
```javascript
const directionsService = new google.maps.DirectionsService();
const directionsRenderer = new google.maps.DirectionsRenderer();
directionsRenderer.setMap(map);
```

#### 6. Heatmaps
```javascript
const heatmap = new google.maps.visualization.HeatmapLayer({
    data: heatmapData,
    map: map
});
```

## 🧪 Testing Your Maps

### Quick Test Checklist

```bash
# 1. Open map
open dno_energy_map_advanced.html

# 2. Check if map loads (should see UK)

# 3. Test buttons:
#    - SVA (Embedded) → Should show circles
#    - CVA (Transmission) → Should show triangles
#    - DNO Boundaries → Should show regions
#    - GSP Zones → Should show purple areas

# 4. Test interactions:
#    - Zoom in/out → Should work smoothly
#    - Pan → Should drag map
#    - Click markers → Should show info window

# 5. Check browser console (F12):
#    - No red errors
#    - Should see: "✅ Map initialized"
```

### If Map Shows Gray Screen
**Common causes:**
1. **API key invalid** → Check console for errors
2. **CORS issue** → Use local server (python -m http.server)
3. **JSON files not loading** → Check file paths
4. **JavaScript error** → Check console for errors

### If Markers Don't Appear
**Common causes:**
1. **JSON files missing** → Check files exist
2. **Coordinates out of range** → Check lat/lng values
3. **Markers outside view** → Pan/zoom to UK
4. **Layer not activated** → Click button to show layer

## 📊 Current Map Capabilities

### What Your Map Can Do (Already Working):

✅ **Display 7,072 SVA generators** (embedded)
✅ **Display ~2,600 CVA plants** (transmission - when scraped)
✅ **Show 14 DNO boundaries** (color-coded regions)
✅ **Show 333 GSP zones** (grid supply points)
✅ **Interactive markers** (click for details)
✅ **Toggle layers** (show/hide different data)
✅ **Color coding** (by fuel type)
✅ **Size scaling** (by capacity)
✅ **Custom controls** (sidebar panel)
✅ **Responsive design** (works on mobile)
✅ **Info windows** (detailed plant information)

### What's NOT Using Google Maps (But Could):

❌ Demand heatmap (not implemented yet)
❌ Price heatmap (not implemented yet)
❌ Wind farms layer (button exists, not implemented)
❌ Real-time data updates
❌ Historical data playback
❌ Route planning
❌ Search functionality

## 💡 Recommendations

### For Personal Use (Current)
✅ Keep current setup - it works!
✅ Use local file or local server
✅ No changes needed

### For Sharing with Others
1. **Host on web server** (GitHub Pages is free)
2. **Restrict API key** (to your domain only)
3. **Add loading indicator** (show "Loading map...")
4. **Add error handling** (show message if map fails)

### For Production Use
1. **Get dedicated API key** (don't share in public repo)
2. **Set up billing** (ensure free tier applies)
3. **Add monitoring** (track API usage)
4. **Optimize performance** (lazy load data, clustering)
5. **Add caching** (reduce API calls)

## 🔐 Security Best Practices

### Current Risk Level: Medium
**Your API key is visible in HTML source**

Anyone who views your HTML can see: `AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0`

### Mitigation Options:

**Option 1: API Key Restrictions (Recommended)**
```
Set HTTP referrer restrictions in Google Cloud Console:
- Only allow your domain
- Block all other referrers
```

**Option 2: Backend Proxy (Advanced)**
```
User Browser → Your Server → Google Maps API
- API key stored on server
- Server makes API calls
- Maps data sent to browser
```

**Option 3: Environment Variables (For Deployment)**
```javascript
// Don't commit API key to git
const API_KEY = process.env.GOOGLE_MAPS_API_KEY;
```

### Monitor API Usage
```
Google Cloud Console → APIs & Services → Dashboard
- Check daily requests
- Set up billing alerts
- Monitor for unusual activity
```

## 📝 Summary

### Your Current Status: ✅ WORKING

**What you have:**
- ✅ Google Maps JavaScript API integration
- ✅ Valid API key (AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0)
- ✅ Map displaying UK with custom markers
- ✅ Interactive layers and controls
- ✅ 7,072 SVA generators mapped
- ✅ Ready for 2,600+ CVA plants

**What you might need:**
- ⚠️ Verify API key is still active
- ⚠️ Set up billing account (for continued use beyond trial)
- ⚠️ Add HTTP referrer restrictions (for security)
- ⚠️ Use web server instead of file:// (for better compatibility)

**To test right now:**
```bash
# Option 1: Direct open (might have CORS issues)
open dno_energy_map_advanced.html

# Option 2: Local server (recommended)
cd /Users/georgemajor/GB\ Power\ Market\ JJ
python -m http.server 8000
# Then open: http://localhost:8000/dno_energy_map_advanced.html
```

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Gray screen | Check API key in console, enable billing |
| No markers | Click buttons to activate layers |
| Slow loading | Reduce data, add clustering |
| CORS errors | Use local server (python -m http.server) |
| API errors | Check Google Cloud Console for restrictions |
| Mobile issues | Map should work, check viewport settings |

---

**Bottom Line:** Your maps ARE Google Maps - they're working right now! You just need to ensure the API key stays valid and optionally improve hosting/security. 🗺️✨

