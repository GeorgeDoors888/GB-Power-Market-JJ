# 🔧 Alternative Methods to Enable Maps JavaScript API

## Issue
Getting error when trying to enable Maps JavaScript API:
```
Failed to load.
There was an error while loading /apis/library/maps-javascript-api.googleapis.com
Request ID: 11827409249515561828
```

---

## 🎯 SOLUTION 1: Try Different Browser/Account

### Method A: Clear Authentication
1. **Sign out** of all Google accounts in your browser
2. **Clear browser cache** (Ctrl+Shift+Delete)
3. **Restart browser**
4. Sign in with account: `george.major@grid-smart.co.uk` (the one that owns the project)
5. Try URL again: https://console.cloud.google.com/apis/library/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9

### Method B: Use Incognito/Private Window
1. Open **Incognito/Private window** (Ctrl+Shift+N in Chrome)
2. Sign in with `george.major@grid-smart.co.uk`
3. Navigate to URL

### Method C: Try Different Browser
- Chrome → Try Firefox or Edge
- Sometimes one browser works when another doesn't

### Method D: Check Account Selection
The error mentions `authuser=3` - you might be signed in with multiple Google accounts.

Try these URLs with different account numbers:
```
https://console.cloud.google.com/apis/library/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9&authuser=0

https://console.cloud.google.com/apis/library/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9&authuser=1

https://console.cloud.google.com/apis/library/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9&authuser=2
```

---

## 🎯 SOLUTION 2: Navigate Via Console Menu

Instead of direct link, navigate manually:

1. Go to main Console: https://console.cloud.google.com/
2. Select project: **inner-cinema-476211-u9** (dropdown at top)
3. Click **☰** menu (top left)
4. Select **APIs & Services** → **Library**
5. Search box: type "**Maps JavaScript API**"
6. Click on "**Maps JavaScript API**"
7. Click **ENABLE** button

---

## 🎯 SOLUTION 3: Enable via gcloud CLI

If you have gcloud CLI installed on your AlmaLinux server:

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project inner-cinema-476211-u9

# Enable Maps JavaScript API
gcloud services enable maps-backend.googleapis.com
gcloud services enable maps-embed-backend.googleapis.com
gcloud services enable maps-javascript-api.googleapis.com

# Verify enabled
gcloud services list --enabled | grep maps
```

**Expected output**:
```
maps-backend.googleapis.com
maps-embed-backend.googleapis.com
maps-javascript-api.googleapis.com
```

---

## 🎯 SOLUTION 4: Use API Enablement Page (Alternative URL)

Try this alternative URL format:
```
https://console.cloud.google.com/apis/api/maps-backend.googleapis.com/overview?project=inner-cinema-476211-u9
```

Or this one:
```
https://console.cloud.google.com/marketplace/product/google/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9
```

---

## 🎯 SOLUTION 5: Check Billing Account

Sometimes APIs won't enable without active billing:

1. Go to: https://console.cloud.google.com/billing/linkedaccount?project=inner-cinema-476211-u9
2. Verify billing account is **active**
3. If not linked, link a billing account
4. Try enabling APIs again

**Note**: Maps JavaScript API has free tier (28,000 map loads/month free), but still requires billing account linked.

---

## 🎯 SOLUTION 6: Check IAM Permissions

You might not have permission to enable APIs:

1. Go to: https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9
2. Find your account: `george.major@grid-smart.co.uk`
3. Check role - need one of:
   - **Owner**
   - **Editor**
   - **Service Usage Admin**
   - **Project IAM Admin**

If you don't have permission, ask project owner to:
- Grant you **Editor** role
- OR enable the APIs themselves

---

## 🎯 SOLUTION 7: Use Alternative - OpenStreetMap

If you absolutely cannot enable Google Maps API, we can switch to **Leaflet.js** (OpenStreetMap) which requires no API key:

This would require modifying `map_sidebarh.html` to use Leaflet instead of Google Maps. It's free, no restrictions, and works well for UK mapping.

**Pros**:
- No API key needed
- No billing required
- No quotas or restrictions
- Works immediately

**Cons**:
- Different API (need to rewrite map code)
- Different styling

Would you like me to create a Leaflet version as fallback?

---

## 🔍 DIAGNOSTIC: Check Current API Status

Run this in terminal to see which APIs are currently enabled:

```bash
# Using gcloud CLI
gcloud services list --enabled --project=inner-cinema-476211-u9 | grep -i map

# Or using Python
python3 << 'EOF'
from google.cloud import bigquery
import subprocess

result = subprocess.run([
    'gcloud', 'services', 'list', 
    '--enabled', 
    '--project=inner-cinema-476211-u9'
], capture_output=True, text=True)

print("Currently enabled Google Maps APIs:")
for line in result.stdout.split('\n'):
    if 'map' in line.lower():
        print(f"  ✅ {line}")

print("\nSearching for Maps JavaScript API...")
if 'maps-javascript-api' in result.stdout:
    print("  ✅ Maps JavaScript API is ENABLED")
else:
    print("  ❌ Maps JavaScript API is NOT enabled")
EOF
```

---

## 🔍 TEST: Check if API is Already Enabled

Maybe it's already enabled and there's just a UI issue? Test with curl:

```bash
# Test Maps API with your key
curl "https://maps.googleapis.com/maps/api/js?key=AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0&v=weekly" 2>&1 | head -20
```

**If you see**:
- `ApiNotActivatedMapError` → API definitely not enabled
- `RefererNotAllowedMapError` → API IS enabled, just domain restrictions
- JavaScript code with `google.maps` → API IS enabled and working!

---

## 🎯 RECOMMENDED ACTION PLAN

Try in this order:

1. **Quick test first** - Run the curl test above to see if API is actually already enabled
   
2. **If not enabled, try gcloud CLI** (fastest if you have gcloud):
   ```bash
   gcloud services enable maps-javascript-api.googleapis.com --project=inner-cinema-476211-u9
   ```

3. **If no gcloud, try alternative browser** - Incognito window with correct account

4. **If browser issues persist, navigate manually** - Don't use direct link, go via menu

5. **Check billing** - Make sure billing account is linked

6. **If all fails, use Leaflet** - I can create OpenStreetMap version (no API key needed)

---

## 🆘 Still Stuck?

**Option A: Have someone with Owner role enable it**
Send this to project owner:
```
Please enable these APIs in project inner-cinema-476211-u9:
- Maps JavaScript API
- Maps Backend API

Run: gcloud services enable maps-javascript-api.googleapis.com maps-backend.googleapis.com --project=inner-cinema-476211-u9
```

**Option B: Switch to Leaflet (OpenStreetMap)**
Let me know and I'll create a version that needs no API keys.

**Option C: Use existing embedded Google Map**
We could use a static iframe with a pre-configured map (limited interactivity).

---

## 📝 What to Try Right Now

**Copy and paste this into terminal:**

```bash
# Test 1: Check if gcloud is installed
which gcloud && echo "✅ gcloud installed" || echo "❌ gcloud not installed"

# Test 2: Check current API status
curl -s "https://maps.googleapis.com/maps/api/js?key=AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0&v=weekly" | head -50

# Test 3: Try enabling via gcloud (if installed)
if which gcloud > /dev/null; then
  echo "Attempting to enable Maps JavaScript API..."
  gcloud services enable maps-javascript-api.googleapis.com --project=inner-cinema-476211-u9 2>&1
  echo "Checking if enabled..."
  gcloud services list --enabled --project=inner-cinema-476211-u9 | grep maps
fi
```

**Then tell me what output you get!**

---

**Last Updated**: 1 January 2026  
**Next Step**: Run the diagnostic commands above and report results
