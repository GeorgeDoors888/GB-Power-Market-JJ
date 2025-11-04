"""
Safety utilities for Drive write operations
Prevents accidental data loss when using full Drive access
"""
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Protected folders that should never be modified
PROTECTED_FOLDERS = os.environ.get("PROTECTED_FOLDERS", "").split(",")
PROTECTED_FOLDERS = [f.strip() for f in PROTECTED_FOLDERS if f.strip()]

# Safety mode - default to true
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
ENABLE_WRITE_OPERATIONS = os.environ.get("ENABLE_WRITE_OPERATIONS", "false").lower() == "true"
MAX_FILES_PER_RUN = int(os.environ.get("MAX_FILES_PER_RUN", "100"))


class SafetyViolation(Exception):
    """Raised when a safety check fails"""
    pass


def check_safety_enabled():
    """Check if write operations are explicitly enabled"""
    if not ENABLE_WRITE_OPERATIONS:
        raise SafetyViolation(
            "Write operations are disabled. Set ENABLE_WRITE_OPERATIONS=true to enable."
        )


def is_protected_path(file_path: str) -> bool:
    """Check if file path contains protected folder names"""
    if not PROTECTED_FOLDERS:
        return False
    
    for protected in PROTECTED_FOLDERS:
        if protected.lower() in file_path.lower():
            return True
    return False


def safe_delete(drive_service, file_id: str, file_name: str = None):
    """
    Safely delete a file with multiple checks
    
    Args:
        drive_service: Google Drive service instance
        file_id: ID of file to delete
        file_name: Optional file name for logging
    """
    check_safety_enabled()
    
    # Get file details if name not provided
    if not file_name:
        file_info = drive_service.files().get(
            fileId=file_id, 
            fields='name,parents,owners'
        ).execute()
        file_name = file_info['name']
    
    # Check if protected
    if is_protected_path(file_name):
        raise SafetyViolation(f"Cannot delete protected file: {file_name}")
    
    if DRY_RUN:
        logger.warning(f"[DRY RUN] Would delete file: {file_name} (ID: {file_id})")
        return
    
    logger.warning(f"⚠️  DELETING file: {file_name} (ID: {file_id})")
    drive_service.files().delete(fileId=file_id).execute()
    logger.info(f"✓ Deleted: {file_name}")


def safe_update(drive_service, file_id: str, body: Dict[str, Any], file_name: str = None):
    """
    Safely update a file with multiple checks
    
    Args:
        drive_service: Google Drive service instance
        file_id: ID of file to update
        body: Update body
        file_name: Optional file name for logging
    """
    check_safety_enabled()
    
    # Get file details if name not provided
    if not file_name:
        file_info = drive_service.files().get(
            fileId=file_id, 
            fields='name,parents,owners'
        ).execute()
        file_name = file_info['name']
    
    # Check if protected
    if is_protected_path(file_name):
        raise SafetyViolation(f"Cannot update protected file: {file_name}")
    
    if DRY_RUN:
        logger.warning(f"[DRY RUN] Would update file: {file_name} (ID: {file_id})")
        logger.debug(f"[DRY RUN] Update body: {body}")
        return
    
    logger.warning(f"⚠️  UPDATING file: {file_name} (ID: {file_id})")
    result = drive_service.files().update(
        fileId=file_id,
        body=body
    ).execute()
    logger.info(f"✓ Updated: {file_name}")
    return result


def safe_batch_operation(items: List[Any], operation_func, operation_name: str = "operation"):
    """
    Safely perform batch operations with rate limiting
    
    Args:
        items: List of items to process
        operation_func: Function to call for each item
        operation_name: Name of operation for logging
    """
    check_safety_enabled()
    
    total = len(items)
    if total > MAX_FILES_PER_RUN:
        raise SafetyViolation(
            f"Batch operation exceeds safety limit: {total} > {MAX_FILES_PER_RUN}. "
            f"Increase MAX_FILES_PER_RUN if needed."
        )
    
    logger.info(f"Starting batch {operation_name}: {total} items")
    
    for i, item in enumerate(items):
        if DRY_RUN:
            logger.info(f"[DRY RUN] [{i+1}/{total}] Would perform {operation_name}")
        else:
            logger.info(f"[{i+1}/{total}] Performing {operation_name}")
            operation_func(item)
        
        # Progress check every 10 items
        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
    
    logger.info(f"✓ Completed batch {operation_name}: {total} items")


def log_write_operation(operation: str, file_id: str, details: str = ""):
    """
    Log all write operations for audit trail
    
    Args:
        operation: Type of operation (delete, update, create, etc.)
        file_id: File ID affected
        details: Additional details
    """
    admin_email = os.environ.get("GOOGLE_WORKSPACE_ADMIN_EMAIL", "unknown")
    log_msg = f"WRITE_OP: user={admin_email}, op={operation}, file_id={file_id}"
    if details:
        log_msg += f", details={details}"
    
    if DRY_RUN:
        log_msg = "[DRY RUN] " + log_msg
    
    logger.warning(log_msg)


# Print safety status on import
if DRY_RUN:
    logger.info("🔒 DRY RUN MODE ENABLED - No actual changes will be made")
if ENABLE_WRITE_OPERATIONS:
    logger.warning("⚠️  WRITE OPERATIONS ENABLED - Changes will be made to Drive")
else:
    logger.info("🔒 WRITE OPERATIONS DISABLED - Set ENABLE_WRITE_OPERATIONS=true to enable")
if PROTECTED_FOLDERS:
    logger.info(f"🛡️  Protected folders: {', '.join(PROTECTED_FOLDERS)}")
