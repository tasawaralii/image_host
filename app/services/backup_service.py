from typing import Any, Dict

try:
    from ..backup import GoogleDriveBackup, backup_to_drive, get_drive_backups
    BACKUP_AVAILABLE = True
    IMPORT_ERROR = None
except Exception as exc:
    GoogleDriveBackup = None
    backup_to_drive = None
    get_drive_backups = None
    BACKUP_AVAILABLE = False
    IMPORT_ERROR = exc


def _ensure_available() -> None:
    if not BACKUP_AVAILABLE:
        raise RuntimeError(str(IMPORT_ERROR))


def backup_full(db_path: str, uploads_dir: str) -> Dict[str, Any]:
    _ensure_available()
    return backup_to_drive(db_path, uploads_dir)


def backup_database(db_path: str) -> Dict[str, Any]:
    _ensure_available()
    backup = GoogleDriveBackup()
    return backup.backup_database(db_path)


def backup_uploads(uploads_dir: str) -> Dict[str, Any]:
    _ensure_available()
    backup = GoogleDriveBackup()
    return backup.backup_uploads(uploads_dir)


def list_backups(limit: int = 10) -> Dict[str, Any]:
    _ensure_available()
    return get_drive_backups(limit)


def delete_backup(folder_id: str) -> Dict[str, Any]:
    _ensure_available()
    backup = GoogleDriveBackup()
    return backup.delete_backup_group(folder_id)


def restore_backup_group(folder_id: str, db_path: str, uploads_dir: str) -> Dict[str, Any]:
    _ensure_available()
    backup = GoogleDriveBackup()
    return backup.restore_group(folder_id, db_path, uploads_dir)
