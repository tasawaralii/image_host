import os
import shutil
import tempfile
import zipfile
from datetime import datetime

from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
OAUTH_CREDENTIALS_FILE = 'google-oauth-token.json'
OAUTH_CLIENT_FILE = 'google-oauth-client.json'
BACKUP_FOLDER_NAME = "Anime Image Service Backups"


class GoogleDriveBackup:
    """Handle backups to Google Drive using OAuth"""

    def __init__(self):
        """Initialize Google Drive service"""
        self.service = None
        self.credentials = None
        self.root_folder_id = None

    def authenticate(self):
        """Authenticate using OAuth (user's personal Google account)"""
        try:
            creds = None

            if os.path.exists(OAUTH_CREDENTIALS_FILE):
                creds = OAuthCredentials.from_authorized_user_file(OAUTH_CREDENTIALS_FILE, SCOPES)

            if not creds or not creds.valid:
                if not os.path.exists(OAUTH_CLIENT_FILE):
                    raise FileNotFoundError(
                        f"OAuth client file not found: {OAUTH_CLIENT_FILE}\n"
                        "Download from Google Cloud Console: APIs & Services > Credentials > OAuth 2.0 Client IDs"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

                with open(OAUTH_CREDENTIALS_FILE, 'w') as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.service = build('drive', 'v3', credentials=creds)
            return True

        except Exception as e:
            raise Exception(f"Google Drive authentication failed: {str(e)}")

    def _ensure_root_folder(self):
        """Create root backup folder if it doesn't exist"""
        if self.root_folder_id:
            return self.root_folder_id

        try:
            query = f"name='{BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id)',
                pageSize=1
            ).execute()

            items = results.get('files', [])
            if items:
                self.root_folder_id = items[0]['id']
                return self.root_folder_id

            folder = self.service.files().create(
                body={'name': BACKUP_FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder'},
                fields='id'
            ).execute()
            self.root_folder_id = folder.get('id')
            return self.root_folder_id
        except HttpError as error:
            raise Exception(f"Failed to create backup folder: {str(error)}")

    def _create_group_folder(self, group_name):
        root_id = self._ensure_root_folder()
        folder = self.service.files().create(
            body={
                'name': group_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [root_id]
            },
            fields='id'
        ).execute()
        return folder.get('id')

    def _upload_file(self, local_path, remote_name, parent_id):
        media = MediaFileUpload(local_path, resumable=True)
        file = self.service.files().create(
            body={'name': remote_name, 'parents': [parent_id]},
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')

    def backup_full(self, db_path, uploads_dir):
        """Backup database and uploads into a single group folder"""
        zip_path = None
        try:
            if not self.service:
                self.authenticate()
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database not found: {db_path}")
            if not os.path.exists(uploads_dir):
                raise FileNotFoundError(f"Uploads directory not found: {uploads_dir}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            group_name = f"backup_{timestamp}"
            group_id = self._create_group_folder(group_name)

            db_name = f"images_db_{timestamp}.db"
            db_file_id = self._upload_file(db_path, db_name, group_id)

            zip_base = f"uploads_{timestamp}"
            zip_path = f"{zip_base}.zip"
            shutil.make_archive(zip_base, 'zip', uploads_dir)
            zip_file_id = self._upload_file(zip_path, zip_path, group_id)

            if os.path.exists(zip_path):
                os.remove(zip_path)

            return {
                "status": "success",
                "group_name": group_name,
                "group_id": group_id,
                "database": {"name": db_name, "file_id": db_file_id},
                "uploads": {"name": zip_path, "file_id": zip_file_id},
                "timestamp": timestamp
            }
        except Exception as e:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
            raise Exception(f"Full backup failed: {str(e)}")

    def list_backup_groups(self, limit=10):
        """List recent backup group folders"""
        try:
            if not self.service:
                self.authenticate()

            root_id = self._ensure_root_folder()
            query = (
                f"'{root_id}' in parents and "
                "mimeType='application/vnd.google-apps.folder' and trashed=false"
            )
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime)',
                pageSize=limit,
                orderBy='createdTime desc'
            ).execute()

            folders = results.get('files', [])
            groups = []
            for folder in folders:
                files = self.service.files().list(
                    q=f"'{folder['id']}' in parents and trashed=false",
                    spaces='drive',
                    fields='files(id, name, size)',
                    pageSize=50
                ).execute().get('files', [])
                groups.append({
                    "folder_id": folder['id'],
                    "folder_name": folder['name'],
                    "created": folder.get('createdTime'),
                    "files": files
                })

            return {"status": "success", "total": len(groups), "groups": groups}
        except Exception as e:
            raise Exception(f"Failed to list backups: {str(e)}")

    def restore_group(self, folder_id, db_path, uploads_dir):
        """Restore database and uploads from a backup group folder"""
        temp_dir = None
        try:
            if not self.service:
                self.authenticate()

            files = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id, name)',
                pageSize=100
            ).execute().get('files', [])

            db_file = next((f for f in files if f['name'].endswith('.db')), None)
            zip_file = next((f for f in files if f['name'].endswith('.zip')), None)

            if not db_file or not zip_file:
                raise FileNotFoundError("Backup group is missing .db or .zip file")

            temp_dir = tempfile.mkdtemp(prefix="backup_restore_")
            db_temp = os.path.join(temp_dir, db_file['name'])
            zip_temp = os.path.join(temp_dir, zip_file['name'])

            self._download_file(db_file['id'], db_temp)
            self._download_file(zip_file['id'], zip_temp)

            if os.path.exists(db_path):
                os.remove(db_path)
            shutil.copy2(db_temp, db_path)

            if os.path.exists(uploads_dir):
                shutil.rmtree(uploads_dir)
            os.makedirs(uploads_dir, exist_ok=True)

            with zipfile.ZipFile(zip_temp, 'r') as zip_ref:
                zip_ref.extractall(uploads_dir)

            return {
                "status": "success",
                "message": "Backup restored successfully"
            }
        except Exception as e:
            raise Exception(f"Restore failed: {str(e)}")
        finally:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)

    def _download_file(self, file_id, destination_path):
        request = self.service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as handle:
            downloader = MediaIoBaseDownload(handle, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    def delete_backup_group(self, folder_id):
        """Delete backup group folder and its contents"""
        try:
            if not self.service:
                self.authenticate()

            files = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id)',
                pageSize=100
            ).execute().get('files', [])

            for file in files:
                self.service.files().delete(fileId=file['id']).execute()

            self.service.files().delete(fileId=folder_id).execute()
            return {"status": "success", "message": "Backup group deleted"}
        except Exception as e:
            raise Exception(f"Failed to delete backup group: {str(e)}")


def backup_to_drive(db_path, uploads_dir):
    """One-liner to backup everything"""
    backup = GoogleDriveBackup()
    return backup.backup_full(db_path, uploads_dir)


def get_drive_backups(limit=10):
    """One-liner to list backup groups"""
    backup = GoogleDriveBackup()
    return backup.list_backup_groups(limit)
