# ⚠️ Full Drive Access Enabled - Safety Guide

## Status
✅ **Full Drive Access Configured**  
🔒 **Safety Features Active**  
⏸️ **Write Operations Disabled by Default**

---

## What's Changed

### OAuth Scopes Updated
```
https://www.googleapis.com/auth/drive                    # Full read/write access
https://www.googleapis.com/auth/spreadsheets            # Sheets access
https://www.googleapis.com/auth/documents               # Docs access
https://www.googleapis.com/auth/presentations           # Slides access
```

### Safety Features Added
✅ **Dry Run Mode** - Test operations without making changes  
✅ **Write Protection** - Must explicitly enable write operations  
✅ **Protected Folders** - Whitelist folders that cannot be modified  
✅ **Batch Limits** - Prevent mass operations gone wrong  
✅ **Audit Logging** - Track all write operations  

---

## How to Use Safely

### Step 1: Enable Domain-Wide Delegation

Update the OAuth scopes in Google Workspace Admin Console:

**URL:** https://admin.google.com/ac/owl/domainwidedelegation

**Client ID:** `108583076839984080568`

**New OAuth Scopes (copy this entire line):**
```
https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/presentations
```

### Step 2: Configure Safety Settings

Edit `.env` file to set your protection levels:

```bash
# Safety Settings
DRY_RUN=true                          # Test mode - no actual changes
ENABLE_WRITE_OPERATIONS=false         # Explicit enable required
MAX_FILES_PER_RUN=100                 # Limit batch operations
PROTECTED_FOLDERS=Legal,HR,Board      # Folders that cannot be modified
```

### Step 3: Test with Dry Run

```bash
# Deploy with safety enabled
scp drive-bq-indexer/.env root@94.237.55.15:/opt/driveindexer/
scp drive-bq-indexer/src/auth/google_auth.py root@94.237.55.15:/opt/driveindexer/src/auth/
scp drive-bq-indexer/src/utils/drive_safety.py root@94.237.55.15:/opt/driveindexer/src/utils/

ssh root@94.237.55.15 '
  docker cp /opt/driveindexer/.env driveindexer:/app/ &&
  docker cp /opt/driveindexer/src/auth/google_auth.py driveindexer:/app/src/auth/ &&
  docker cp /opt/driveindexer/src/utils/drive_safety.py driveindexer:/app/src/utils/ &&
  docker restart driveindexer
'

# Test operations in dry run mode
ssh root@94.237.55.15 'docker exec driveindexer python3 -c "
from src.utils.drive_safety import *
print('Safety Status:')
print(f'  DRY_RUN: {DRY_RUN}')
print(f'  WRITE_OPERATIONS: {ENABLE_WRITE_OPERATIONS}')
print(f'  MAX_FILES: {MAX_FILES_PER_RUN}')
print(f'  PROTECTED: {PROTECTED_FOLDERS}')
"'
```

### Step 4: Enable Write Operations (When Ready)

```bash
# Update .env to allow writes
ssh root@94.237.55.15 'cat >> /opt/driveindexer/.env << EOF
DRY_RUN=false
ENABLE_WRITE_OPERATIONS=true
EOF'

# Apply changes
ssh root@94.237.55.15 'docker cp /opt/driveindexer/.env driveindexer:/app/ && docker restart driveindexer'
```

---

## Safety Features Explained

### 1. Dry Run Mode
**Default:** `DRY_RUN=true`

All write operations are logged but NOT executed:
```
[DRY RUN] Would delete file: report.pdf (ID: abc123)
[DRY RUN] Would update file: data.xlsx (ID: def456)
```

### 2. Write Protection
**Default:** `ENABLE_WRITE_OPERATIONS=false`

Even with full Drive access, writes are blocked until explicitly enabled:
```python
# Will raise SafetyViolation error:
safe_delete(drive, file_id, "report.pdf")
# Error: Write operations are disabled. Set ENABLE_WRITE_OPERATIONS=true
```

### 3. Protected Folders
**Default:** `PROTECTED_FOLDERS=Legal,HR,Board`

Critical folders cannot be modified:
```python
safe_delete(drive, file_id, "Legal/contract.pdf")
# Error: Cannot delete protected file: Legal/contract.pdf
```

### 4. Batch Operation Limits
**Default:** `MAX_FILES_PER_RUN=100`

Prevents mass operations:
```python
safe_batch_operation(1000_files, delete_func, "delete")
# Error: Batch operation exceeds safety limit: 1000 > 100
```

### 5. Audit Logging

All write operations are logged:
```
WRITE_OP: user=george@upowerenergy.uk, op=delete, file_id=abc123
WRITE_OP: user=george@upowerenergy.uk, op=update, file_id=def456
```

---

## Using Safety Functions

### Import the safety module:
```python
from src.utils.drive_safety import (
    safe_delete,
    safe_update,
    safe_batch_operation,
    is_protected_path,
    log_write_operation
)
```

### Example: Safe Delete
```python
# Instead of:
drive.files().delete(fileId=file_id).execute()

# Use:
safe_delete(drive, file_id, "report.pdf")
# Checks: protection, dry-run, logging
```

### Example: Safe Update
```python
# Instead of:
drive.files().update(fileId=file_id, body=update_body).execute()

# Use:
safe_update(drive, file_id, update_body, "data.xlsx")
# Checks: protection, dry-run, logging
```

### Example: Safe Batch
```python
def delete_file(file):
    safe_delete(drive, file['id'], file['name'])

safe_batch_operation(
    items=files_to_delete,
    operation_func=delete_file,
    operation_name="delete old files"
)
# Checks: batch limit, progress logging
```

---

## Recommended Workflow

### Phase 1: Read-Only Testing (Current State)
```bash
DRY_RUN=true
ENABLE_WRITE_OPERATIONS=false
```
- ✅ Complete Drive indexing
- ✅ Test all read operations
- ✅ Verify domain-wide delegation working

### Phase 2: Dry Run Testing
```bash
DRY_RUN=true
ENABLE_WRITE_OPERATIONS=true
```
- ✅ Test write operations in simulation mode
- ✅ Review logs to see what would happen
- ✅ Adjust protected folders if needed

### Phase 3: Controlled Writes
```bash
DRY_RUN=false
ENABLE_WRITE_OPERATIONS=true
MAX_FILES_PER_RUN=10  # Start small!
```
- ✅ Enable actual writes
- ✅ Test on small batches first
- ✅ Monitor logs carefully

### Phase 4: Production Use
```bash
DRY_RUN=false
ENABLE_WRITE_OPERATIONS=true
MAX_FILES_PER_RUN=100
PROTECTED_FOLDERS=Legal,HR,Board,Compliance
```
- ✅ Increase batch limits as needed
- ✅ Add more protected folders
- ✅ Regular backup checks

---

## Emergency: Disable Write Access

### If something goes wrong:

**Option 1: Disable in code (instant)**
```bash
ssh root@94.237.55.15 'docker exec driveindexer sh -c "
  echo ENABLE_WRITE_OPERATIONS=false >> /app/.env &&
  docker restart driveindexer
"'
```

**Option 2: Revoke in Admin Console**
1. Go to: https://admin.google.com/ac/owl/domainwidedelegation
2. Find Client ID: `108583076839984080568`
3. Click "Delete" or "Edit" to remove scopes

**Option 3: Disable service account**
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=jibber-jabber-knowledge
2. Click on `jibber-jabber-knowledge@appspot.gserviceaccount.com`
3. Click "Disable"

---

## Current State

**Configured:**
- ✅ Full Drive access scopes in code
- ✅ Safety utilities created
- ✅ Protection settings in .env
- ⏸️ **Not yet deployed to UpCloud**
- ⏸️ **Not yet authorized in Admin Console**

**Next Steps:**
1. Update OAuth scopes in Google Workspace Admin Console
2. Deploy updated code to UpCloud
3. Test with scan_all_drive.py (should see thousands of files)
4. Run full indexing in read-only mode first
5. Only enable write operations when specifically needed

---

## Questions?

- **"Should I enable writes now?"** → No, complete indexing first (read-only)
- **"What if I need to modify files?"** → Enable DRY_RUN=true first, test, then enable ENABLE_WRITE_OPERATIONS=true
- **"Can I undo changes?"** → Google Drive keeps version history for 30 days
- **"Is this safe?"** → Yes, with all safety features enabled and gradual rollout

---

**Remember:** Full Drive access is powerful but risky. Always test with DRY_RUN=true first! 🔒
