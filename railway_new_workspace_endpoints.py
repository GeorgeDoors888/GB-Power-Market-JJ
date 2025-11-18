"""
Copy these 3 new endpoints to the BOTTOM of api_gateway.py
Add them just BEFORE the @app.on_event("startup") section
"""

# ============================================
# GOOGLE WORKSPACE ENDPOINTS (NEW)
# ============================================

@app.get("/workspace/health")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def workspace_health(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Check if Workspace delegation is working"""
    try:
        gc = get_sheets_client()
        if not gc:
            return {
                "status": "error",
                "message": "Could not initialize Sheets client"
            }
        
        # Try to access the dashboard
        sheet = gc.open_by_key(SHEETS_ID)
        
        return {
            "status": "healthy",
            "message": "Workspace access working!",
            "services": {
                "sheets": "ok",
                "drive": "ok"
            },
            "dashboard": {
                "title": sheet.title,
                "worksheets": len(sheet.worksheets())
            }
        }
    except Exception as e:
        logger.error(f"Workspace health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/workspace/dashboard")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
def get_dashboard_info(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Get GB Energy Dashboard information"""
    log_action("WORKSPACE_DASHBOARD_ACCESS", {"spreadsheet_id": SHEETS_ID})
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
        
        worksheets = []
        for ws in sheet.worksheets():
            worksheets.append({
                "id": ws.id,
                "title": ws.title,
                "rows": ws.row_count,
                "cols": ws.col_count
            })
        
        return {
            "success": True,
            "title": sheet.title,
            "spreadsheet_id": sheet.id,
            "url": sheet.url,
            "worksheets": worksheets,
            "total_worksheets": len(worksheets)
        }
    except Exception as e:
        logger.error(f"Dashboard access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspace/read_sheet")
@limiter.limit(f"{RATE_LIMIT_MIN}/minute")
async def read_sheet_data(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Read data from any worksheet in the dashboard"""
    body = await request.json()
    worksheet_name = body.get('worksheet_name', 'Dashboard')
    cell_range = body.get('range', '')
    
    log_action("WORKSPACE_READ_SHEET", {
        "worksheet": worksheet_name,
        "range": cell_range
    })
    
    try:
        gc = get_sheets_client()
        if not gc:
            raise HTTPException(status_code=503, detail="Sheets client not available")
        
        sheet = gc.open_by_key(SHEETS_ID)
        worksheet = sheet.worksheet(worksheet_name)
        
        if cell_range:
            data = worksheet.get(cell_range)
        else:
            data = worksheet.get_all_values()
        
        return {
            "success": True,
            "worksheet_name": worksheet_name,
            "rows": len(data),
            "cols": len(data[0]) if data else 0,
            "data": data[:100]  # Limit to first 100 rows
        }
    except Exception as e:
        logger.error(f"Read sheet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
