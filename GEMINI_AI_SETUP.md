# 🤖 Setup Guide: Ask Gemini AI Analysis

## What This Does

The "Ask Gemini" feature reads your current power market data and uses Google's Gemini AI to provide:
- **Key observations** from the data
- **Grid health assessment**
- **Renewable performance analysis**
- **Market insights** (prices, balancing costs)
- **Concerns & opportunities**
- **Actionable recommendations**

The AI analysis is written directly to your sheet below the data tables.

---

## 🔑 Setup: Get Your Gemini API Key (Free!)

### Step 1: Get API Key (2 minutes)

1. Go to: **https://makersuite.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (looks like: `AIzaSyD...`)

### Step 2: Configure the Key

**Option A: Environment Variable** (Recommended)
```bash
# Add to your ~/.zshrc or ~/.bash_profile
export GEMINI_API_KEY='your-api-key-here'

# Then reload
source ~/.zshrc
```

**Option B: File** (Easier for testing)
```bash
cd ~/GB\ Power\ Market\ JJ
echo "your-api-key-here" > gemini_api_key.txt
```

### Step 3: Test It
```bash
cd ~/GB\ Power\ Market\ JJ
python3 ask_gemini_analysis.py
```

Should see:
```
🤖 ASK GEMINI: ANALYZE POWER MARKET DATA
✅ Connected to sheet
✅ Connected to Gemini
📊 GEMINI ANALYSIS
...
```

---

## 📦 Install Gemini Library (If Needed)

```bash
cd ~/GB\ Power\ Market\ JJ
python3 -m pip install --user google-generativeai
```

---

## 🚀 How to Use

### Method 1: Run the Script
```bash
cd ~/GB\ Power\ Market\ JJ
python3 ask_gemini_analysis.py
```

Wait 10-20 seconds, then refresh your sheet to see the analysis.

### Method 2: Add to Update Workflow
```bash
# Refresh data AND get AI analysis
python3 update_analysis_bi_enhanced.py && python3 ask_gemini_analysis.py
```

### Method 3: Automate (Optional)
```bash
# Add to crontab - refresh data + AI analysis every hour
0 * * * * cd ~/GB\ Power\ Market\ JJ && python3 update_analysis_bi_enhanced.py && python3 ask_gemini_analysis.py >> gemini_analysis.log 2>&1
```

---

## 📊 What Gemini Sees

The script sends Gemini:
- **Summary metrics**: Total generation, renewable %, frequency, prices
- **Generation mix**: Top 10 fuel types with percentages
- **Recent frequency**: Last 5 measurements
- **Recent prices**: Last 5 market prices
- **Recent balancing**: Last 5 balancing cost records

Gemini analyzes this in the context of UK power market operations.

---

## 📝 Example Analysis Output

```
🤖 GEMINI AI ANALYSIS

Generated: 2025-10-31 15:45:23

Key Observations:
- Renewable generation at 50.6% is strong, meeting UK targets
- Grid frequency stable at 49.965 Hz with no critical events
- Average market price of £37.46/MWh is below seasonal average
- CCGT providing 31.2% baseload, typical for autumn period

Grid Health Assessment:
- EXCELLENT: All frequency measurements within normal range (49.8-50.2 Hz)
- Grid stability rated "Normal" with no warnings
- No evidence of supply stress or capacity shortages

Renewable Performance:
- Wind contributing 25.8% (strong autumn winds)
- Solar at 6.6% (typical for late October)
- Nuclear providing steady 18.4% low-carbon baseload
- Combined renewables+nuclear exceeding 50% target

Market Insights:
- £37.46/MWh average suggests good supply-demand balance
- No extreme price spikes observed in recent periods
- Balancing costs moderate, indicating efficient grid operation
- Low volatility suggests stable weather and demand patterns

Concerns & Opportunities:
CONCERNS:
- Frequency slightly below nominal 50 Hz (49.965 Hz) - monitor trend
- Gas dependence at 31.2% remains high

OPPORTUNITIES:
- Strong renewable performance - good time for flexible demand
- Low prices favorable for industrial consumers
- Grid stability allows for planned maintenance windows

Recommendations:
FOR GRID OPERATORS:
1. Monitor frequency trend - consider reserve activation if dips continue
2. Maintain current balancing approach - working efficiently
3. Use stable conditions for planned outages/maintenance

FOR TRADERS:
1. Low price environment - good for long positions in near-term
2. Monitor wind forecasts - strong contribution likely to continue
3. Consider flexibility services during high renewable periods

FOR CONSUMERS:
1. Favorable pricing environment for high-demand operations
2. High renewable % aligns with sustainability targets
3. Grid stability supports reliable supply for critical operations
```

---

## 🔧 Customizing the Analysis

Edit `ask_gemini_analysis.py` to:

### Change which data is included
```python
# Line ~85: Adjust how much data to send
gen_data = sheet.get('A18:G27')  # Top 10 rows
# Change to:
gen_data = sheet.get('A18:G37')  # Top 20 rows
```

### Change the analysis focus
```python
# Line ~115: Modify the prompt
prompt = f"""You are an expert UK power market analyst...
```

Add sections like:
- "Focus on trading opportunities"
- "Identify grid stress indicators"
- "Compare to historical trends"

### Change where analysis appears
```python
# Line ~165: Modify start row
analysis_start_row = 115
# Change to different row
```

---

## 💡 Tips

### 1. Run After Data Updates
```bash
# Best workflow
python3 update_analysis_bi_enhanced.py  # Refresh data first
python3 ask_gemini_analysis.py          # Then analyze
```

### 2. Different Time Periods
Change the date range in the sheet (cell B5), refresh data, then ask Gemini:
```bash
# User changes B5 to "1 Month" in sheet
python3 update_analysis_bi_enhanced.py
python3 ask_gemini_analysis.py
```

### 3. Compare Analyses Over Time
```bash
# Save analysis output
python3 ask_gemini_analysis.py > analysis_$(date +%Y%m%d_%H%M).txt
```

### 4. Batch Analysis
```bash
# Analyze multiple time periods
for period in "1 Week" "1 Month" "3 Months"; do
    echo "Analyzing $period..."
    # Manually set B5 to $period in sheet
    # Then run:
    python3 update_analysis_bi_enhanced.py
    python3 ask_gemini_analysis.py
    sleep 30  # Rate limiting
done
```

---

## 🔍 Troubleshooting

### "API key not found"
```bash
# Check if key is set
echo $GEMINI_API_KEY

# Or check file exists
cat ~/GB\ Power\ Market\ JJ/gemini_api_key.txt
```

### "Module 'google.generativeai' not found"
```bash
python3 -m pip install --user google-generativeai
```

### "Quota exceeded"
- Gemini has rate limits (free tier: 60 requests/minute)
- Wait 1 minute between runs
- Or upgrade to paid tier

### "Invalid API key"
- Regenerate key at https://makersuite.google.com/app/apikey
- Make sure no spaces before/after key
- Check key hasn't been deleted in Google AI Studio

### Analysis looks generic
- Make sure data refreshed first (`update_analysis_bi_enhanced.py`)
- Check sheet has real data (not placeholders)
- Verify date range is recent

---

## 🎯 What You Get

### In Terminal
- Full analysis text
- Formatted with markdown
- Easy to read and share

### In Google Sheet
- Analysis written to row 115+
- Timestamp of when generated
- Formatted for readability
- Updates each time you run

### Benefits
- **Expert insights** without manual analysis
- **Spot trends** you might miss
- **Actionable recommendations** for operations/trading
- **Context-aware** analysis specific to UK power market
- **Fast** - results in 10-20 seconds

---

## 📚 Related Files

- `ask_gemini_analysis.py` - Main script
- `create_analysis_bi_enhanced.py` - Sheet setup (includes button)
- `update_analysis_bi_enhanced.py` - Data refresh
- `gemini_api_key.txt` - Your API key (don't commit to git!)

---

## 🔐 Security Note

**Never commit your API key to git!**

Add to `.gitignore`:
```bash
echo "gemini_api_key.txt" >> .gitignore
```

If using environment variable, it's automatically secure.

---

**Ready to try?**
```bash
python3 ask_gemini_analysis.py
```

Your AI power market analyst awaits! 🤖⚡
