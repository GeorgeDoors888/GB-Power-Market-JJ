# Constraint Map Deployment Notes

## ✅ Deployed Successfully

**Current Deployment (Version 8):**
- Version: 8 ✅ **ACTIVE WITH API KEY**
- Date: 25 Nov 2025, 00:47
- Deployment ID: `AKfycbw5DSYuky8TrsgMPOsl-arEdQ96gnYHd19f9W6KdUIdbsXJpfH5zlYu8mWNPh1OmcY9`
- Web App URL: https://script.google.com/macros/s/AKfycbw5DSYuky8TrsgMPOsl-arEdQ96gnYHd19f9W6KdUIdbsXJpfH5zlYu8mWNPh1OmcY9/exec

**Previous Deployment (Version 7):**
- Version: 7
- Date: 25 Nov 2025, 00:31
- Deployment ID: `AKfycbyq7s0Ga37EV8HY1nrsV0Zt2bNgBIPClTbrt7kL0W1k_tqhCMeEodZvZIRNqiLOzTCA`
- Web App URL: https://script.google.com/macros/s/AKfycbyq7s0Ga37EV8HY1nrsV0Zt2bNgBIPClTbrt7kL0W1k_tqhCMeEodZvZIRNqiLOzTCA/exec

## 🔑 Google Maps API Key

**✅ CONFIGURED** in constraint_map.html (line 110):
```html
<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDjw_YjobTs0DCbZwl6p1vXbPSxG6YQNCE"></script>
```

## 📍 How to Use

 ##C#l iFcrko mt hGe o*o*gEldei tS*h*e eictons (:p
e1nc.il )O pneextn t o yVeorusrio n Dashboard spreadsheet
2. Menu: **🗺️ Constraint Map** → **📍 Show Interactive Map**
3. Map opens in right sidebar

### Direct Web App Access:
Visit: https://script.google.com/macros/s/AKfycbyq7s0Ga37EV8HY1nrsV0Zt2bNgBIPClTbrt7kL0W1k_tqhCMeEodZvZIRNqiLOzTCA/exec

## �� To Update the Deployment

After making changes to constraint_map.html:

1. Go to Apps Script editor
2. Click: **Deploy** → **Manage deployments**
3.7
4. Change "Version": **New version**
5. Add description: "Updated API key" (or your change description)
6. Click **Deploy**
7. Copy the new Deployment ID

## 🎨 Current Features

- ✅ Live constraint data from DDaasrhkb otahredm er oUwIs
 -1 1??-?1 2A6u
t-o -??e?f rrersehr sceahpra bsicleiathyp
r
## 🐛 Ia bsicleiathyp
r
## 🐛 Ia bsicleiathyp
r
## 🐛 Ia bsicleiathyp
r
## 🐛 Ia bsicleiathyp
r
## 🐛 Ia bsicleiathyp
r
## 🐛 Ia bsicleiathyp
r
## ??? oIdded.egds.`e g-d sB.a`cek egn-dd  fsuBncti.oan`sc e(kg eetgCnon-sdtdr a ifnstuDBantcat,i .ooan`sc e(kg eetgCnon-sdtdr a ifnstuDBantcat,i .ooan`sc e(kg eetgCnon-sdtdr a ifnstuDBantcat,i .ooan`sc e(kg eetgCnon-sdtdr a ifnstuDBantcat,i .ooan`sc e(kg eetgCnon-sdtdr a ifnstuDBantcat,i .ooan`sc e(kg eetgCnon-sdtdr a ifnstuDBantcat,i .ooan`sc e(kg eetgCnon-sdtdr a ifnstuDBantcat,i .ooan`sc e(kg eetgCnon-sdtdr a nOpen, etc.)
- `ConstraintMap.html` - Map UI (this file with API key)

## 🆘 Troubleshooting

### "Map failed to load"
- API key issue - check it's enabled in Google Cloud Console
- Enable: Google Maps JavaScript API

### "No data"
- Run: `python3 update_constraints_dashboard_v2.py`
- Wait 30 seconds
- Refresh map

### "Authorization required"
- Apps Script needs authorization first time
- Run: `onOpen()` function in Apps Script
- Complete authorization flow

## 🎉 Success Indicators

When working correctly:
- Map shows UK with constraint boundaries
- Circles are color-coded by utilization
- Clicking circles shows popup with details
- Layer checkboxes toggle visibility
- "Updated: [time]" shows in top right

## 📊 Data Flow

```
BigQuery (uk_constraints.constraint_flows_da)
    ↓
update_constraints_dashboard_v2.py (every 5 min)
    ↓
Dashboard Sheet Rows 116-126
    ↓
Apps Script getConstraintData()
    ↓
constraint_map.html (Google Maps visualizatnio ns)i
d e b a rr
r`
`r``


`-r-`-`



*
*`N-erx-t` -D`e
p
l
o
y*m
e*n`tN*-*e: Version 8 (when you update the HTML with API key)
