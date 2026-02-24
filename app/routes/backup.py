from fastapi import APIRouter, Header, HTTPException

from ..config import API_KEY, DB_PATH, UPLOAD_DIR
from ..services.backup_service import (
    backup_database,
    backup_full,
    backup_uploads,
    delete_backup,
    list_backups,
    restore_backup_group,
)

router = APIRouter(prefix="/backup")


def _require_api_key(x_api_key: str) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")


@router.post("/backup")
async def backup_full_endpoint(x_api_key: str = Header(None)):
    _require_api_key(x_api_key)
    try:
        results = backup_full(DB_PATH, UPLOAD_DIR)
        return {"status": "success", "message": "Full backup completed", "details": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(exc)}")


@router.get("/backups")
async def list_backups_endpoint(x_api_key: str = Header(None), limit: int = 10):
    _require_api_key(x_api_key)
    try:
        return list_backups(limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(exc)}")


@router.post("/restore/{folder_id}")
async def restore_backup_group_endpoint(folder_id: str, x_api_key: str = Header(None)):
    _require_api_key(x_api_key)
    try:
        return restore_backup_group(folder_id, DB_PATH, UPLOAD_DIR)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(exc)}")


@router.delete("/{folder_id}")
async def delete_backup_endpoint(folder_id: str, x_api_key: str = Header(None)):
    _require_api_key(x_api_key)
    try:
        return delete_backup(folder_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(exc)}")
