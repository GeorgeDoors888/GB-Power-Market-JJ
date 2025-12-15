# Clasp Setup for Both Spreadsheets

## Step 1: Login to clasp (one-time)
Run in VS Code terminal (SSH: dell):
```bash
cd ~/GB-Power-Market-JJ
clasp login
```
Follow browser prompt to authenticate with your Google account.

## Step 2: Spreadsheet IDs
- Sheet 1 (Main Dashboard): 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
- Sheet 2 (Secondary): 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

## Step 3: Create separate Apps Script projects
```bash
# For Sheet 1
mkdir -p apps_script_sheet1
cd apps_script_sheet1
clasp create --type sheets --title "Sheet1 Dashboard Scripts" --parentId 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

# For Sheet 2 (already configured)
cd ../appsscript_v3
clasp pull
```

## For AI Design:
AI can generate:
- Code.gs files with menu creation, formatting functions
- Chart configurations
- Conditional formatting rules
- Data validation
- Custom functions

Deploy with: clasp push && clasp deploy
