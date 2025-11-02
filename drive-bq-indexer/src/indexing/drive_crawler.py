from __future__ import annotations
import logging, time
from typing import Iterator
from ..auth.google_auth import drive_client

log = logging.getLogger(__name__)

def iter_drive_files(query: str) -> Iterator[dict]:
    """Paginate Google Drive listing."""
    svc = drive_client()
    page_token = None
    fields = "nextPageToken, files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink,owners,parents)"
    while True:
        resp = (
            svc.files()
            .list(q=query, pageToken=page_token, fields=fields,
                  pageSize=1000, includeItemsFromAllDrives=True,
                  supportsAllDrives=True)
            .execute()
        )
        for f in resp.get("files", []):
            yield f
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.2)
